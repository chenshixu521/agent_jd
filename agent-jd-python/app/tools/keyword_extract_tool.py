from collections import OrderedDict

SKILL_DICT = [
    "Java", "Spring Boot", "Spring Cloud", "MyBatis", "MySQL", "Redis", "Docker", "Kubernetes",
    "Python", "FastAPI", "LangChain", "LangGraph", "OpenAI", "通义", "FAISS", "RAG", "Vue3", "Element Plus",
    "微服务", "分布式", "消息队列", "RabbitMQ", "RocketMQ", "Kafka", "JWT", "MyBatis-Plus",
]


def keyword_extract_tool(text: str) -> dict:
    normalized = text or ""
    found = OrderedDict()
    lower_text = normalized.lower()
    for skill in SKILL_DICT:
        if skill.lower() in lower_text or skill in normalized:
            found[skill] = True
    return {"keywords": list(found.keys()), "count": len(found)}
