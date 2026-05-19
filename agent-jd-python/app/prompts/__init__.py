from app.core.settings import settings
from app.prompts.loader import PromptRegistry

prompt_registry = PromptRegistry(settings.prompt_dir)
