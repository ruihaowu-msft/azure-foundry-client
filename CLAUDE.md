# CLAUDE.md — 必读 · Always-Follow

> ⚠️ **本文件由 Claude Code 在每个会话开始时自动加载。**
> 在本仓库做任何事——**尤其是搭建或修改 pipeline**——之前，必须先读完本文件并严格遵守。
> 这是唯一事实来源（single source of truth）：改约定就改本文件。
>
> 主体是下面的「Custom Instructions」（一直遵守的个人工作规范）；
> 末尾的「本仓库专属补充」是针对本 Foundry 仓库、**已实测**的落地细节。

---

# Copilot Custom Instructions — Ruihao (William) Wu

## Who I am / context
- I'm an Azure AI Solution Engineer building proof-of-concepts (PoCs), not production systems: image attribute extraction, video highlights, and content moderation on Azure AI.
- Primary language: Python. I also read C#/.NET samples.
- I work heavily with AI-assisted coding but I'm still strengthening my raw-coding fundamentals. **I must understand and be able to debug everything I ship — so help me learn, don't hide complexity.**

## How to write code for me
- Prefer clear, readable code over clever one-liners. Use descriptive names.
- **Never ship happy-path only** — include error handling and the obvious edge cases. If you intentionally skip something, say so explicitly.
- After writing any non-trivial code, add a **short plain-language explanation** of what each part does and why, so I can verify and learn it.
- Comment the *why*, not the obvious *what*. Keep comments concise.
- Start with the **simplest approach that works**; only mention a more advanced option if it actually matters.
- Keep changes small and scoped. Don't refactor things I didn't ask about.

## Accuracy and honesty (I can't always catch your mistakes yet)
- **Do not invent** APIs, SDK methods, parameters, or `az` CLI flags. If you're not sure something exists, say so and tell me to verify against the official Microsoft docs.
- State your assumptions explicitly: api-version, SDK version, region, model/deployment name.
- When you use a non-obvious Azure API, point me to the relevant doc page.
- If a request is ambiguous, ask me instead of guessing.

## Azure AI patterns to follow
- For extracting structured data from images, use **Structured Outputs with a strict JSON schema / Pydantic model** (e.g. `client.beta.chat.completions.parse(...)`), **not** "please return JSON" prompting.
- **Always set `max_tokens` / `max_completion_tokens`, and set it *generously* above the expected output length.** It's a ceiling, not a reservation — short outputs still cost only what they actually generate, so erring high is safe. After each call, check `finish_reason`: if it's `length`, the output was truncated — raise the limit and retry instead of parsing a cut-off response.
- Model repeated items as **arrays of objects** (not stringified JSON); use **enums** for categorical fields; write **affirmative, specific** field descriptions.
- For blob-triggered pipelines, use the **Event Grid-based** trigger, not the legacy polling trigger.

## Security and data (hard rules — never break these)
- **Never hardcode** keys, secrets, or connection strings. Read from environment variables; prefer **Managed Identity / Key Vault**.
- **Never put real keys, customer data, or PII** in code, comments, logs, or examples — always use placeholders.
- **Flag anything touching faces / biometrics / personal data** as needing human + compliance review. Don't silently design around it.
- Don't auto-accept low-confidence AI extractions — route them to human review.

## Cost discipline
- Flag anything that could incur ongoing Azure cost.
- Remind me to **tear down resource groups** (`az group delete`) after a demo.

## How I iterate on accuracy
- When I tune the extraction schema or prompts, remind me to **change one variable at a time** and re-run my eval set before concluding anything.

## Communication
- Teach as you go: briefly explain the Azure concept behind what we're doing when it's relevant.
- You may explain code and concepts to me in **Chinese** (中文母语); keep code, identifiers, and comments in English.

---

## 本仓库专属补充 (This repo · 已实测，2026-06-24)

> 这一节把上面的通用规范落到本仓库的真实环境。所有结论都已对**已安装的 SDK / 真实部署**实测，未臆造。

### 统一入口
- 所有对 Foundry **模型 / 服务** 的调用走 `FoundryClient`（[foundry.py](foundry.py)），不要在 pipeline 里手写 endpoint / 拼 URL / 自己管 token。
- 配置（端点、部署名）从 [.env](.env) 读取，不写死。`.gitignore` 已排除 `.env*`；每次提交前确认 `git status` 里没有 `.env`。
- 鉴权：本地 `az login`（`DefaultAzureCredential`，scope `https://ai.azure.com/.default`）；或在 `.env` 设 `AZURE_OPENAI_KEY`。**符合上面"prefer Managed Identity"** —— 部署到 Azure 时用托管标识即可，无需改代码。

### ⚠️ 当前部署 `gpt-5.4-pro-1` 只支持 Responses API（实测）
调 chat completions 返回 `400 - "The requested operation is unsupported."`。
因此上面「Azure AI patterns」里两条以 **chat completions** 为前提的规则，在**本部署**上要按下表映射。
（下列等价 API 均已对 `openai==2.8.0` + 真实部署**实测通过**；换 chat-capable 部署时则用你原文的 chat 写法。）

| 你的规则（chat 写法） | 本部署的 Responses 等价写法（已实测） |
| --- | --- |
| `client.beta.chat.completions.parse(...)` 做结构化输出 | `client.responses.parse(..., text_format=YourPydanticModel)` → 读 `resp.output_parsed` |
| 设 `max_tokens` / `max_completion_tokens` | 设 `max_output_tokens`（同样"宁可设大"） |
| 检查 `finish_reason == "length"` | 检查 `resp.status == "incomplete"` 且 `resp.incomplete_details.reason == "max_output_tokens"`，截断则调大上限重试 |

```python
# 本部署上的结构化输出（已实测：status=completed，output_parsed 为 Pydantic 实例）
from pydantic import BaseModel
from foundry import FoundryClient

class ImageAttributes(BaseModel):   # 严格 schema：用数组装重复项、枚举装分类字段、字段描述写肯定句
    ...

fc = FoundryClient()
resp = fc.openai().responses.parse(
    model=fc.model,
    input="...",                    # 图片/文本输入
    text_format=ImageAttributes,
    max_output_tokens=4000,         # 宁可设大；按预期输出长度留足余量
)
if resp.status == "incomplete":     # 截断检测：别去解析被切断的结果
    raise RuntimeError(f"truncated: {resp.incomplete_details}")
data = resp.output_parsed           # -> ImageAttributes 实例
```

> 结构化输出的**原则不变**（strict schema / Pydantic / 数组 / 枚举），只是 API 入口从 chat 换成 responses。
> 官方文档请核对 Microsoft Learn：「Azure OpenAI — Structured outputs」与「Responses API」（需要的话我帮你拉当前链接）。

### 参考
- 客户端用法：[foundry.py](foundry.py) 头部注释、[FOUNDRY_CLIENT_GUIDE.md](FOUNDRY_CLIENT_GUIDE.md)
- 本地运行 / 环境：[INSTRUCTIONS.md](INSTRUCTIONS.md)
