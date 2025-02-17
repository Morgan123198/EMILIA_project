from langchain_openai import ChatOpenAI
from .config import get_settings

settings = get_settings()

# Initialize shared LLM instance
llm = ChatOpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.OPENROUTER_API_KEY,
    model=settings.LLM_MODEL,
)
