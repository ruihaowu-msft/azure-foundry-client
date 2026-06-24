# Azure Foundry 通用客户端使用指南

这是一个通用的 Azure Foundry 客户端模块，用于简化调用 Azure Foundry 上的模型或服务。

## 文件说明

- **azure_foundry_client.py**: 核心客户端模块，包含 `AzureFoundryClient` 类
- **examples.py**: 使用示例
- **.env.example**: 环境变量模板

## 快速开始

### 1. 配置环境

复制 `.env.example` 为 `.env`，填入你的 Azure Foundry 配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入：
- `AZURE_FOUNDRY_ENDPOINT`: 你的 Azure OpenAI 端点
- `AZURE_FOUNDRY_DEPLOYMENT`: 你的模型部署名称

### 2. 基本使用

```python
from azure_foundry_client import AzureFoundryClient

# 创建客户端
client = AzureFoundryClient()

# 简单查询
answer = client.simple_query("你好，你叫什么名字？")
print(answer)
```

### 3. 主要功能

#### 简单查询
```python
client = AzureFoundryClient()
response = client.simple_query("法国的首都是什么？")
```

#### 多轮对话
```python
conversation = []

# 第一轮
reply1, conversation = client.conversation(
    conversation,
    "你能给我讲一个笑话吗？"
)

# 第二轮 (可以引用前面的内容)
reply2, conversation = client.conversation(
    conversation,
    "这很有趣，能再讲一个吗？"
)
```

#### 自定义参数
```python
messages = [{"role": "user", "content": "写一首诗"}]

response = client.chat_completion(
    messages,
    temperature=1.5,      # 创意度 (0-2)
    max_tokens=200,       # 最大输出长度
    top_p=0.95           # 核心采样参数
)
```

#### 系统提示词
```python
messages = [
    {"role": "system", "content": "你是一个编程专家"},
    {"role": "user", "content": "如何优化 Python 代码？"}
]

response = client.chat_completion(messages)
```

## 认证方式

### 方式 1: Azure Identity (推荐)

使用 Azure CLI 登录：
```bash
az login
```

然后直接使用客户端：
```python
client = AzureFoundryClient()  # 使用 Azure Identity
```

### 方式 2: API Key

设置环境变量或直接传入：
```python
client = AzureFoundryClient(
    api_key="your-api-key",
    use_credential=False
)
```

## 环境变量

支持以下环境变量：

| 变量名 | 说明 | 默认值 |
|------|------|--------|
| `AZURE_FOUNDRY_ENDPOINT` | Azure OpenAI 端点 | https://test18u2313.services.ai.azure.com/openai/v1 |
| `AZURE_FOUNDRY_DEPLOYMENT` | 模型部署名称 | gpt-5.4-pro-1 |
| `AZURE_OPENAI_KEY` | API 密钥 (非必需) | - |

## 常见参数

- **temperature** (0-2): 控制随机性，0 表示确定性，2 表示最随机
- **max_tokens**: 最大输出令牌数，限制回复长度
- **top_p** (0-1): 核心采样参数，控制多样性

## 运行示例

```bash
# 运行所有示例
python azure_foundry_client.py

# 运行特定示例
python examples.py
```

## 错误处理

客户端会捕获异常并打印错误信息：

```python
try:
    response = client.simple_query("你好")
except Exception as e:
    print(f"调用失败: {e}")
```

## 高级用法

### 自定义客户端
```python
client = AzureFoundryClient(
    endpoint="https://your-endpoint.openai.azure.com/v1",
    deployment_name="your-deployment",
    api_key="your-key"
)
```

### 传递额外参数
```python
response = client.chat_completion(
    messages,
    presence_penalty=0.5,
    frequency_penalty=0.5,
    # 其他 OpenAI API 支持的参数
)
```

## 依赖项

```
azure-identity>=1.25.0
openai>=2.8.0
```

## 更多信息

- [Azure AI Foundry 文档](https://learn.microsoft.com/en-us/azure/ai-services/)
- [OpenAI Python 库](https://github.com/openai/openai-python)
- [Azure Identity 库](https://github.com/Azure/azure-sdk-for-python)
