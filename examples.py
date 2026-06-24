"""
Azure Foundry 客户端使用示例
演示如何用通用客户端调用 Azure Foundry 上的模型
"""

from azure_foundry_client import AzureFoundryClient


def example_simple_query():
    """示例 1: 简单查询"""
    print("=" * 50)
    print("示例 1: 简单查询")
    print("=" * 50)
    
    client = AzureFoundryClient()
    response = client.simple_query("请用一句话解释什么是人工智能")
    print(f"回答: {response}\n")


def example_conversation():
    """示例 2: 多轮对话"""
    print("=" * 50)
    print("示例 2: 多轮对话")
    print("=" * 50)
    
    client = AzureFoundryClient()
    conversation = []
    
    # 第一轮
    question1 = "Python 中什么是列表解析？"
    print(f"用户: {question1}")
    answer1, conversation = client.conversation(conversation, question1)
    print(f"助手: {answer1}\n")
    
    # 第二轮 (可以引用前面的内容)
    question2 = "能给我举个实际的例子吗？"
    print(f"用户: {question2}")
    answer2, conversation = client.conversation(conversation, question2)
    print(f"助手: {answer2}\n")


def example_custom_parameters():
    """示例 3: 自定义参数"""
    print("=" * 50)
    print("示例 3: 自定义参数")
    print("=" * 50)
    
    client = AzureFoundryClient()
    
    # 使用自定义参数
    messages = [{"role": "user", "content": "写一首关于春天的短诗"}]
    
    response = client.chat_completion(
        messages,
        temperature=1.2,  # 提高创意度
        max_tokens=200,
        top_p=0.95
    )
    
    print(f"回答:\n{response.choices[0].message.content}\n")


def example_with_system_prompt():
    """示例 4: 使用系统提示词"""
    print("=" * 50)
    print("示例 4: 系统提示词")
    print("=" * 50)
    
    client = AzureFoundryClient()
    
    messages = [
        {"role": "system", "content": "你是一个专业的编程助手，回答尽量简洁明了。"},
        {"role": "user", "content": "怎样在 Python 中处理异常？"}
    ]
    
    response = client.chat_completion(messages)
    print(f"回答:\n{response.choices[0].message.content}\n")


def example_batch_queries():
    """示例 5: 批量查询"""
    print("=" * 50)
    print("示例 5: 批量查询")
    print("=" * 50)
    
    client = AzureFoundryClient()
    
    queries = [
        "什么是 REST API？",
        "什么是 GraphQL？",
        "REST 和 GraphQL 有什么区别？"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"问题 {i}: {query}")
        answer = client.simple_query(query)
        print(f"回答: {answer}\n")


if __name__ == "__main__":
    # 运行示例 (取消注释要运行的示例)
    
    example_simple_query()
    # example_conversation()
    # example_custom_parameters()
    # example_with_system_prompt()
    # example_batch_queries()
