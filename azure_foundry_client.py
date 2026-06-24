"""
通用 Azure Foundry 客户端模块
用于调用 Azure Foundry 上的模型或服务
"""

import os
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI, AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


class AzureFoundryClient:
    """
    Azure Foundry 通用客户端
    
    支持：
    - 单轮对话
    - 多轮对话（对话历史）
    - 函数调用
    - 自定义参数
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_key: Optional[str] = None,
        use_credential: bool = True,
    ):
        """
        初始化 Azure Foundry 客户端
        
        Args:
            endpoint: Azure OpenAI 端点 URL (如果为 None，从环境变量 AZURE_FOUNDRY_ENDPOINT 读取)
            deployment_name: 部署名称 (如果为 None，从环境变量 AZURE_FOUNDRY_DEPLOYMENT 读取)
            api_key: API 密钥 (如果为 None 且 use_credential=False，从环境变量 AZURE_OPENAI_KEY 读取)
            use_credential: 是否使用 Azure Identity (默认 True)
        """
        # 从环境变量读取配置
        self.endpoint = endpoint or os.getenv("AZURE_FOUNDRY_ENDPOINT", "https://test18u2313.services.ai.azure.com/openai/v1")
        self.deployment_name = deployment_name or os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "gpt-5.4-pro-1")
        
        # 初始化 OpenAI 客户端
        if use_credential:
            # 使用 Azure Identity 进行身份验证
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), 
                "https://ai.azure.com/.default"
            )
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=token_provider
            )
        else:
            # 使用 API Key
            api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=api_key
            )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性 (0-2)
            max_tokens: 最大输出令牌数
            top_p: 核心采样参数
            **kwargs: 其他参数传递给 OpenAI API
        
        Returns:
            返回完整的响应对象
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs
            )
            return response
        except Exception as e:
            print(f"错误：调用模型失败 - {str(e)}")
            raise
    
    def simple_query(self, query: str, **kwargs) -> str:
        """
        简单的单轮查询接口
        
        Args:
            query: 用户查询内容
            **kwargs: 其他参数传递给 chat_completion
        
        Returns:
            模型的回复文本
        """
        messages = [{"role": "user", "content": query}]
        response = self.chat_completion(messages, **kwargs)
        return response.choices[0].message.content
    
    def conversation(
        self,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        **kwargs
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        多轮对话接口
        
        Args:
            conversation_history: 对话历史列表
            user_message: 当前用户消息
            **kwargs: 其他参数传递给 chat_completion
        
        Returns:
            返回 (模型回复, 更新后的对话历史)
        """
        # 添加用户消息到历史
        conversation_history.append({"role": "user", "content": user_message})
        
        # 调用模型
        response = self.chat_completion(conversation_history, **kwargs)
        assistant_message = response.choices[0].message.content
        
        # 添加助手回复到历史
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message, conversation_history
    
    def function_call(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        支持函数调用的请求
        
        Args:
            messages: 消息列表
            tools: 工具/函数定义列表
            tool_choice: 工具选择策略 ("auto", "required", 或具体的工具名称)
            **kwargs: 其他参数
        
        Returns:
            返回完整的响应对象
        """
        response = self.chat_completion(
            messages,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs
        )
        return response


# 快速启动函数
def quick_start():
    """快速启动示例"""
    client = AzureFoundryClient()
    
    # 简单查询
    print("=== 简单查询示例 ===")
    answer = client.simple_query("法国的首都是什么？")
    print(f"回答: {answer}\n")
    
    # 多轮对话
    print("=== 多轮对话示例 ===")
    conversation_history = []
    
    # 第一轮对话
    reply1, conversation_history = client.conversation(
        conversation_history,
        "请给我讲一个关于机器学习的笑话"
    )
    print(f"用户: 请给我讲一个关于机器学习的笑话")
    print(f"助手: {reply1}\n")
    
    # 第二轮对话 (模型可以访问上下文)
    reply2, conversation_history = client.conversation(
        conversation_history,
        "能解释一下这个笑话吗?"
    )
    print(f"用户: 能解释一下这个笑话吗?")
    print(f"助手: {reply2}\n")


if __name__ == "__main__":
    quick_start()
