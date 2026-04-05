"""
LLM 客户端封装

使用阿里百炼平台 API (OpenAI 兼容模式)
"""
from openai import OpenAI
from config import settings


def get_llm_client() -> OpenAI:
    """
    获取 LLM 客户端
    
    使用阿里百炼平台的 OpenAI 兼容接口
    """
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url
    )


def chat_completion(messages: list, temperature: float = 0.7) -> str:
    """
    调用对话模型
    
    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        temperature: 温度参数
    
    Returns:
        模型回复内容
    """
    client = get_llm_client()
    
    response = client.chat.completions.create(
        model=settings.dashscope_llm_model,
        messages=messages,
        temperature=temperature
    )
    
    return response.choices[0].message.content


def get_embeddings(texts: list) -> list:
    """
    获取文本嵌入向量
    
    Args:
        texts: 文本列表
    
    Returns:
        嵌入向量列表
    """
    client = get_llm_client()
    
    response = client.embeddings.create(
        model=settings.dashscope_embedding_model,
        input=texts
    )
    
    return [item.embedding for item in response.data]


# 便捷函数
def diagnose_with_llm(fault_context: str, retrieved_knowledge: str) -> dict:
    """
    使用 LLM 进行故障诊断
    
    Args:
        fault_context: 故障上下文
        retrieved_knowledge: 检索到的知识
    
    Returns:
        结构化诊断结果
    """
    messages = [
        {
            "role": "system",
            "content": "你是一个制造业设备故障诊断专家。基于提供的知识，分析故障原因并给出处置建议。输出JSON格式。"
        },
        {
            "role": "user",
            "content": f"""
故障信息:
{fault_context}

相关知识:
{retrieved_knowledge}

请输出JSON格式诊断结果，包含:
- fault_name: 故障名称
- probable_causes: 可能原因列表(含rank, cause, confidence)
- recommended_steps: 推荐排查步骤
- risk_level: 风险级别(低/中/高)
- should_escalate: 是否建议升级(bool)
- spare_parts: 建议备件列表(含name, model)
"""
        }
    ]
    
    result = chat_completion(messages, temperature=0.3)
    
    # 解析 JSON 结果
    import json
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # 如果返回的不是标准 JSON，尝试提取 JSON 部分
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"无法解析 LLM 输出: {result}")


# 测试代码
if __name__ == "__main__":
    # 测试配置
    print(f"API Base URL: {settings.dashscope_base_url}")
    print(f"LLM Model: {settings.dashscope_llm_model}")
    print(f"Embedding Model: {settings.dashscope_embedding_model}")
    
    # 测试对话
    if settings.dashscope_api_key:
        print("\n测试对话...")
        response = chat_completion([
            {"role": "user", "content": "你好，请简单介绍一下自己"}
        ])
        print(f"回复: {response}")
        
        # 测试嵌入
        print("\n测试嵌入...")
        embeddings = get_embeddings(["测试文本", "另一个测试"])
        print(f"嵌入维度: {len(embeddings[0])}")
    else:
        print("\n未配置 DASHSCOPE_API_KEY，跳过测试")
