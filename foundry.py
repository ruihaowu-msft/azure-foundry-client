"""
通用 Azure AI Foundry 客户端 (foundry.py)
=========================================

一个文件、零额外依赖（仅需 openai + azure-identity，已安装），即可统一调用
你 Azure AI Foundry 上的 **模型 (model)** 与 **服务 / 智能体 (service / agent)**。

设计来自对官方 SDK `azure-ai-projects` (2.x) `get_openai_client()` 的源码核对，
两条数据平面路由完全一致：

    模型 (model)            ->  {endpoint}/openai/v1
    服务/智能体 (agent)      ->  {project_endpoint}/agents/{name}/endpoint/protocols/openai?api-version=v1
    鉴权 (auth)             ->  Bearer Token，scope = https://ai.azure.com/.default

也就是说：Foundry 把"模型"和"服务"都统一收敛到了一个 OpenAI 兼容接口上，
本文件直接基于已安装的 openai SDK 复刻这两条路由，因此无需安装 azure-ai-projects。

用法 (quick start)
------------------
    az login                                   # 先登录（或设置 AZURE_OPENAI_KEY）
    python foundry.py                          # 跑内置冒烟测试

    from foundry import FoundryClient
    fc = FoundryClient()                       # 自动读取 .env
    print(fc.chat("法国的首都是哪里？"))         # 调模型
    print(fc.run_agent("my-agent", "你好"))     # 调服务/智能体

依赖：openai>=2.8.0, azure-identity>=1.25.0   （均已安装）
可选：az login 用于本地凭据；或在 .env 中设置 AZURE_OPENAI_KEY 用密钥鉴权。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator
from urllib.parse import urlparse

from openai import OpenAI


# --------------------------------------------------------------------------- #
# .env 加载（零依赖，不需要 python-dotenv）                                      #
# --------------------------------------------------------------------------- #
def load_dotenv(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> None:
    """把 .env 里的 KEY=VALUE 读进 os.environ。已存在的变量默认不覆盖。"""
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if override or key not in os.environ:
            os.environ[key] = val


# --------------------------------------------------------------------------- #
# 端点解析                                                                      #
# --------------------------------------------------------------------------- #
def _account_base(endpoint: str) -> str:
    """从任意 Foundry 端点取出账号级主机： https://<res>.services.ai.azure.com"""
    u = urlparse(endpoint)
    return f"{u.scheme}://{u.netloc}"


# --------------------------------------------------------------------------- #
# 主客户端                                                                      #
# --------------------------------------------------------------------------- #
class FoundryClient:
    """
    Azure AI Foundry 通用客户端：一个对象同时覆盖「调模型」与「调服务/智能体」。

    参数
    ----
    project_endpoint : str | None
        Foundry **项目** 端点，例如
        https://<res>.services.ai.azure.com/api/projects/<project>
        默认从环境变量读取（见 _resolve_endpoint）。智能体调用需要它。
    model : str | None
        默认模型 / 部署名，默认读取 AZURE_FOUNDRY_DEPLOYMENT。
    credential : TokenCredential | None
        Azure 凭据；为 None 时用 DefaultAzureCredential()（支持 az login / 托管标识）。
    api_key : str | None
        若提供则用 API Key 鉴权（优先于 token）；否则用 Bearer Token。
        默认读取 AZURE_OPENAI_KEY。
    api_version : str
        智能体路由所需的 api-version，默认 "v1"。
    load_env : bool
        是否自动加载当前目录的 .env，默认 True。
    """

    AUTH_SCOPE = "https://ai.azure.com/.default"

    def __init__(
        self,
        *,
        project_endpoint: str | None = None,
        model: str | None = None,
        credential: Any | None = None,
        api_key: str | None = None,
        api_version: str = "v1",
        load_env: bool = True,
    ) -> None:
        if load_env:
            load_dotenv()

        self.project_endpoint = self._resolve_endpoint(project_endpoint)
        self.account_base = _account_base(self.project_endpoint)
        self.model = model or os.getenv("AZURE_FOUNDRY_DEPLOYMENT") or os.getenv(
            "MODEL_DEPLOYMENT_NAME", "gpt-5.4-pro-1"
        )
        self.api_version = api_version
        self._api_key = api_key or os.getenv("AZURE_OPENAI_KEY") or None
        self._credential = credential
        self._auth: str | Callable[[], str] | None = None  # 懒加载
        self._clients: dict[str, OpenAI] = {}              # base_url -> OpenAI 缓存

    # ----- 端点 / 鉴权 ----------------------------------------------------- #
    @staticmethod
    def _resolve_endpoint(explicit: str | None) -> str:
        ep = (
            explicit
            or os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT")   # azd / Foundry 默认变量
            or os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
            or os.getenv("AZURE_FOUNDRY_ENDPOINT")
        )
        if not ep:
            raise ValueError(
                "未找到 Foundry 端点。请在 .env 设置 AZURE_EXISTING_AIPROJECT_ENDPOINT，"
                "或构造时传入 project_endpoint=..."
            )
        return ep.rstrip("/")

    def _auth_value(self) -> str | Callable[[], str]:
        """返回 api_key 字符串，或一个自动刷新的 Bearer Token 提供器（callable）。"""
        if self._auth is not None:
            return self._auth
        if self._api_key:
            self._auth = self._api_key
        else:
            # 延迟导入，未装 azure-identity 时也能用 API Key 路径
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            cred = self._credential or DefaultAzureCredential()
            self._auth = get_bearer_token_provider(cred, self.AUTH_SCOPE)
        return self._auth

    def _client_for(self, base_url: str, default_query: dict | None = None) -> OpenAI:
        cache_key = base_url + ("?" + str(default_query) if default_query else "")
        if cache_key not in self._clients:
            self._clients[cache_key] = OpenAI(
                base_url=base_url,
                api_key=self._auth_value(),   # 字符串或 token 提供器，openai SDK 均支持
                default_query=default_query,
            )
        return self._clients[cache_key]

    # ----- 底层 OpenAI 客户端：模型 / 智能体 ------------------------------- #
    def openai(self) -> OpenAI:
        """模型推理用的 OpenAI 客户端，base_url = {account}/openai/v1（与官方示例一致）。"""
        return self._client_for(f"{self.account_base}/openai/v1")

    def agent_openai(self, agent_name: str) -> OpenAI:
        """绑定到某个 Foundry 智能体/服务的 OpenAI 客户端（preview 路由）。"""
        base = f"{self.project_endpoint}/agents/{agent_name}/endpoint/protocols/openai"
        return self._client_for(base, default_query={"api-version": self.api_version})

    # ===================================================================== #
    #  模型 (MODEL)：chat / responses / embeddings                          #
    # ===================================================================== #
    @staticmethod
    def _as_messages(prompt_or_messages: str | list[dict], system: str | None) -> list[dict]:
        if isinstance(prompt_or_messages, str):
            msgs: list[dict] = [{"role": "user", "content": prompt_or_messages}]
        else:
            msgs = list(prompt_or_messages)
        if system and not (msgs and msgs[0].get("role") == "system"):
            msgs = [{"role": "system", "content": system}, *msgs]
        return msgs

    def chat(
        self,
        prompt_or_messages: str | list[dict],
        *,
        system: str | None = None,
        model: str | None = None,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Chat Completions。prompt 可以是字符串或标准 messages 列表。
        - stream=True 返回逐块文本的生成器
        - raw=True   返回完整响应对象（用于读 tool_calls / usage 等）
        - 其余 kwargs 透传：temperature / max_tokens / tools / tool_choice ...

        注意：部分较新部署（如 GPT-5 / 推理类模型）**只支持 Responses API**，
        调 chat 会返回 400 "operation is unsupported"。这类部署请改用 respond()。
        """
        messages = self._as_messages(prompt_or_messages, system)
        model = model or self.model
        client = self.openai()
        if stream:
            return self._stream_chat(client, model, messages, **kwargs)
        resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
        return resp if raw else resp.choices[0].message.content

    @staticmethod
    def _stream_chat(client: OpenAI, model: str, messages: list[dict], **kwargs: Any) -> Iterator[str]:
        for chunk in client.chat.completions.create(
            model=model, messages=messages, stream=True, **kwargs
        ):
            if chunk.choices and (delta := chunk.choices[0].delta) and delta.content:
                yield delta.content

    def respond(
        self,
        input: str | list,
        *,
        model: str | None = None,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Responses API（新一代接口；run_model.py 用的就是它）。
        GPT-5 / 推理类等"仅支持 Responses"的部署用这个最稳。
        - stream=True 返回逐块文本的生成器
        - raw=True   返回完整响应对象
        """
        client = self.openai()
        model = model or self.model
        if stream:
            return self._stream_responses(client, model, input, **kwargs)
        resp = client.responses.create(model=model, input=input, **kwargs)
        return resp if raw else self._response_text(resp)

    @staticmethod
    def _stream_responses(client: OpenAI, model: str, input: Any, **kwargs: Any) -> Iterator[str]:
        for ev in client.responses.create(model=model, input=input, stream=True, **kwargs):
            if getattr(ev, "type", None) == "response.output_text.delta":
                yield ev.delta

    @staticmethod
    def _response_text(resp: Any) -> str:
        """从 Responses 对象里稳健地取出文本。"""
        text = getattr(resp, "output_text", None)
        if text:
            return text
        parts: list[str] = []
        for item in getattr(resp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                t = getattr(c, "text", None)
                if t:
                    parts.append(t)
        return "".join(parts)

    def embed(
        self, texts: str | Iterable[str], *, model: str | None = None, **kwargs: Any
    ) -> list[list[float]]:
        """文本向量化。model 需为已部署的 embedding 模型（如 text-embedding-3-small）。"""
        items = [texts] if isinstance(texts, str) else list(texts)
        resp = self.openai().embeddings.create(
            model=model or self.model, input=items, **kwargs
        )
        return [d.embedding for d in resp.data]

    # ===================================================================== #
    #  服务 / 智能体 (SERVICE / AGENT)                                       #
    # ===================================================================== #
    def run_agent(
        self,
        agent_name: str,
        input: str | list,
        *,
        raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        调用 Foundry 上托管的 **智能体 / 服务**（preview）。
        智能体自带模型与指令，这里走它的 Responses 路由。
        """
        client = self.agent_openai(agent_name)
        resp = client.responses.create(input=input, **kwargs)
        return resp if raw else self._response_text(resp)

    # ----- 万能逃生口 ------------------------------------------------------ #
    def raw_openai(self, *, agent_name: str | None = None) -> OpenAI:
        """直接拿到底层 OpenAI 客户端，自己调任意接口（model 或 agent）。"""
        return self.agent_openai(agent_name) if agent_name else self.openai()


# --------------------------------------------------------------------------- #
# 冒烟测试                                                                      #
# --------------------------------------------------------------------------- #
def _smoke_test() -> None:
    fc = FoundryClient()
    print(f"项目端点 : {fc.project_endpoint}")
    print(f"模型端点 : {fc.account_base}/openai/v1")
    print(f"默认模型 : {fc.model}\n")

    print("=== 1) 调模型 · Responses API（推荐，兼容性最好） ===")
    print(fc.respond("用一句话介绍 Azure AI Foundry。"), "\n")

    print("=== 2) 调模型 · 流式（Responses 流式） ===")
    for piece in fc.respond("从 1 数到 5。", stream=True):
        print(piece, end="", flush=True)
    print("\n")

    print("=== 3) 调模型 · Chat Completions ===")
    try:
        print(fc.chat("法国的首都是哪里？", system="你是简洁的中文助手。"), "\n")
    except Exception as e:  # 该部署可能仅支持 Responses
        print(f"(部署 {fc.model} 不支持 chat completions，用 respond() 即可)\n    {e}\n")

    # 智能体/服务路由属 preview，需有已部署的 agent，按需取消注释：
    # print("=== 4) 调服务 · agent ===")
    # print(fc.run_agent("<your-agent-name>", "你好"))


if __name__ == "__main__":
    _smoke_test()
