"""
Azure Foundry 高级用法示例
包括会话管理、日志记录、错误处理等
"""

import json
import logging
from datetime import datetime
from typing import List, Dict
from azure_foundry_client import AzureFoundryClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConversationManager:
    """对话管理器，支持保存和加载对话历史"""
    
    def __init__(self, client: AzureFoundryClient):
        self.client = client
        self.conversation = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "messages_count": 0
        }
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        self.conversation.append({"role": role, "content": content})
        self.metadata["messages_count"] += 1
    
    def send_message(self, user_message: str, **kwargs) -> str:
        """发送用户消息并获取回复"""
        logger.info(f"用户: {user_message[:50]}...")
        
        reply, self.conversation = self.client.conversation(
            self.conversation,
            user_message,
            **kwargs
        )
        
        logger.info(f"助手: {reply[:50]}...")
        return reply
    
    def save_to_file(self, filename: str) -> None:
        """保存对话到 JSON 文件"""
        data = {
            "metadata": self.metadata,
            "conversation": self.conversation
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"对话已保存到 {filename}")
    
    def load_from_file(self, filename: str) -> None:
        """从 JSON 文件加载对话"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data.get("metadata", {})
        self.conversation = data.get("conversation", [])
        
        logger.info(f"对话已从 {filename} 加载")
    
    def get_summary(self) -> Dict:
        """获取对话摘要"""
        return {
            "total_messages": len(self.conversation),
            "user_messages": sum(1 for m in self.conversation if m["role"] == "user"),
            "assistant_messages": sum(1 for m in self.conversation if m["role"] == "assistant"),
            "created_at": self.metadata.get("created_at")
        }


def example_conversation_manager():
    """示例: 使用对话管理器"""
    print("=" * 60)
    print("示例: 对话管理器")
    print("=" * 60)
    
    client = AzureFoundryClient()
    manager = ConversationManager(client)
    
    # 进行对话
    questions = [
        "什么是机器学习？",
        "能简化一下你的解释吗？",
        "给我举个例子"
    ]
    
    for question in questions:
        reply = manager.send_message(question)
        print(f"\n用户: {question}")
        print(f"助手: {reply}")
        print()
    
    # 打印摘要
    summary = manager.get_summary()
    print("对话摘要:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # 保存对话
    manager.save_to_file("conversation_history.json")


def example_error_handling():
    """示例: 错误处理"""
    print("=" * 60)
    print("示例: 错误处理")
    print("=" * 60)
    
    try:
        client = AzureFoundryClient()
        
        # 处理长文本
        long_query = "请总结一下" + "这是一个很长的文本。" * 100
        logger.info(f"发送查询，长度: {len(long_query)}")
        
        response = client.simple_query(
            long_query,
            max_tokens=100
        )
        print(f"回答: {response}\n")
        
    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)


def example_batch_processing():
    """示例: 批量处理"""
    print("=" * 60)
    print("示例: 批量处理")
    print("=" * 60)
    
    client = AzureFoundryClient()
    
    # 多个查询
    queries = [
        "用一句话解释什么是 AI",
        "用一句话解释什么是 ML",
        "用一句话解释什么是 DL"
    ]
    
    results = []
    for i, query in enumerate(queries, 1):
        logger.info(f"处理查询 {i}/{len(queries)}")
        try:
            response = client.simple_query(query)
            results.append({
                "query": query,
                "response": response,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"查询失败: {e}")
            results.append({
                "query": query,
                "error": str(e),
                "status": "failed"
            })
    
    # 保存结果
    with open("batch_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！结果已保存到 batch_results.json")
    print(f"成功: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"失败: {sum(1 for r in results if r['status'] == 'failed')}")


def example_context_window():
    """示例: 利用上下文窗口"""
    print("=" * 60)
    print("示例: 上下文窗口")
    print("=" * 60)
    
    client = AzureFoundryClient()
    
    # 构建上下文
    context = """
    你是一个编程教师。以下是今天的课程主题：
    - 主题: Python 列表推导
    - 难度: 初级
    - 时长: 30 分钟
    """
    
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": "请解释列表推导的基本语法"}
    ]
    
    response = client.chat_completion(messages)
    print(f"回答:\n{response.choices[0].message.content}\n")


if __name__ == "__main__":
    # 运行示例
    example_conversation_manager()
    # example_error_handling()
    # example_batch_processing()
    # example_context_window()
