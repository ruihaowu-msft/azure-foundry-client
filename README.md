# Foundry Media Pipeline Prototype

这是一个前期 prototype，用来把未来客户项目里最关键的链路先固定下来：

1. 接收上传后的媒体资产元数据
2. 调用 Azure AI Foundry / Content Understanding 分析
3. 产出结构化 JSON / Pydantic 对象
4. 按输出类型路由到不同结果目录

当前版本先把“中间层”搭好，入口和真实客户平台解耦。后面无论客户从 Azure Blob、SharePoint、内部平台还是 Web App 上传文件，都可以接到同一条分析链路上。

## 当前能力

- `mock` 模式：本地直接跑通完整流程
- `foundry` 模式：预留真实 Foundry Content Understanding HTTP adapter
- Pydantic 数据契约
- 结构化输出落盘
- 事件入口适配：Blob-style event payload
- Function handler 骨架
- 回调出口适配：本地 capture / HTTP callback
- 基于媒体类型和标签的输出路由
- 单元测试覆盖核心路由逻辑

## 目录

```text
src/media_pipeline/
  models.py        # Pydantic 数据模型
  config.py        # 环境配置
  analyzers.py     # Mock / Foundry analyzer
  ingestion.py     # 上传事件 -> PipelineInput
  classifier.py    # 输出分类与路由
  storage.py       # 结果写盘
  delivery.py      # 回传给客户系统
  pipeline.py      # 主编排器
  function_app.py  # Azure Function 风格入口
  cli.py           # 本地运行入口
tests/
samples/
output/
```

## 建议的云上接法

生产版建议按下面的形态落地：

- 上传层：Azure Blob Storage
- 事件层：Blob 事件 / Event Grid
- 编排层：Azure Functions 或容器化 worker
- 分析层：Content Understanding + Azure OpenAI / 其他 Foundry 模型
- 结果层：Blob / Cosmos DB / SQL / 客户 API 回传

这个 prototype 现在先做的是“编排层 + 分析层 + 结果层 contract”。

## 环境准备

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

## 本地 mock 跑法

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
.venv/bin/python -m media_pipeline.cli process \
  --file samples/invoice-sample.pdf \
  --mode mock
```

## 本地事件入口跑法

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
.venv/bin/python -m media_pipeline.cli process-event \
  --event-file samples/blob-event.json
```

## Foundry 模式

先配置环境变量：

```bash
export CONTENT_UNDERSTANDING_ENDPOINT="https://<resource>.services.ai.azure.com"
export CONTENT_UNDERSTANDING_ANALYZER_ID="prebuilt-tax.us.w4"
export AZURE_AI_TOKEN="<bearer-token>"
```

然后运行：

```bash
.venv/bin/python -m media_pipeline.cli process \
  --file samples/invoice-sample.pdf \
  --source-uri "https://<public-or-signed-url>" \
  --mode foundry
```

说明：

- 这里默认使用 Entra bearer token，而不是静态 key。
- 实际生产里更推荐 Managed Identity 或你已经跑通的 Automation / Function identity。
- `foundry` 模式下，`source-uri` 需要是 Foundry 服务可访问的 `https://` 地址，不能是本地 `file://` 路径。

## AI 协作自动化

这个项目现在带的是一套 **双 Foundry 模型、只上报不自动改代码** 的 PR 自动化骨架：

- [`AGENTS.md`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/AGENTS.md:1)：项目 review 规则
- [`.github/prompts/foundry-review.md`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/.github/prompts/foundry-review.md:1)：通用 reviewer 提示词
- [`scripts/foundry_review.py`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/scripts/foundry_review.py:1)：调用 Azure Foundry reviewer 模型的脚本
- [`.github/workflows/foundry-dual-review.yml`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/.github/workflows/foundry-dual-review.yml:1)：双 reviewer PR workflow

### 运行方式

当 PR 被打开、更新、重新打开或标记为 ready for review 时：

1. Foundry reviewer A 自动跑 review
2. Foundry reviewer B 自动跑 review
3. 两边都会把结果回写到同一个 PR 里，并且会更新已有 bot comment，而不是不停堆新评论
4. workflow **不会自动改代码**

### 需要配置的 GitHub variables / secrets

Repository variables:

- `FOUNDRY_REVIEWER_A_ENDPOINT`
- `FOUNDRY_REVIEWER_A_MODEL`
- `FOUNDRY_REVIEWER_B_ENDPOINT`
- `FOUNDRY_REVIEWER_B_MODEL`

Repository secrets:

- `FOUNDRY_REVIEWER_A_API_KEY` 或 `FOUNDRY_REVIEWER_A_BEARER_TOKEN`
- `FOUNDRY_REVIEWER_B_API_KEY` 或 `FOUNDRY_REVIEWER_B_BEARER_TOKEN`

### 公司环境下的本地 smoke test

本地 reviewer key 和 endpoint 现在默认放在这个文件里：

- [`.env.reviewers`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/.env.reviewers:1)

模板保留在这里：

- [`.env.reviewers.example`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/.env.reviewers.example:1)
- [`config/reviewer-models.template.toml`](/Users/williamwu/scratch/foundry-media-pipeline-prototype/config/reviewer-models.template.toml:1)

你现在直接编辑 `.env.reviewers` 就行，把下面 8 个值填掉：

- `FOUNDRY_REVIEWER_A_ENDPOINT`
- `FOUNDRY_REVIEWER_A_MODEL`
- `FOUNDRY_REVIEWER_A_API_KEY` 或 `FOUNDRY_REVIEWER_A_BEARER_TOKEN`
- `FOUNDRY_REVIEWER_B_ENDPOINT`
- `FOUNDRY_REVIEWER_B_MODEL`
- `FOUNDRY_REVIEWER_B_API_KEY` 或 `FOUNDRY_REVIEWER_B_BEARER_TOKEN`

如果你走 bearer token，本地先登录 Azure，再拿 token：

```bash
az login
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
```

然后把 `TOKEN` 填进 `.env.reviewers` 对应的 `*_BEARER_TOKEN`。

#### 方式 A：一键跑两个 reviewer

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
python3 scripts/run_dual_review_local.py
```

输出会写到：

- `output/local-review/foundry_reviewer_a-output.md`
- `output/local-review/foundry_reviewer_b-output.md`

#### 方式 B：单独测一个 reviewer

先准备一个最小 prompt，然后直连你自己的 Foundry reviewer 模型：

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
python3 scripts/foundry_review.py \
  --endpoint "https://<your-resource>.openai.azure.com" \
  --model "<your-reviewer-deployment>" \
  --prompt-file samples/reviewer-smoke.md \
  --output-file /tmp/reviewer-smoke-out.md \
  --api-key "<your-foundry-key>"
```

如果你走 Entra token，就把 `--api-key` 换成 `--bearer-token`。

### 当前边界

- 这套 workflow 现在是纯 review / reporting 流程
- 如果 reviewer 检查出问题，先在 PR comment 里上报，不会直接改代码
- 真正的修复动作应该在你看完报告后，再显式决定要不要做

## 后续最值得补的 5 件事

1. 增加 Blob 事件入口 adapter
2. 补 Azure Functions 真正的 trigger 包装层
3. 补异步任务状态表，支持视频长任务轮询
4. 增加“回传给客户系统”的重试、签名、幂等机制
5. 把输出从本地文件切到 Blob / Cosmos DB / 客户 API
