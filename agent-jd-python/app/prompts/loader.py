from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template
from pydantic import BaseModel

from app.core.errors import AgentError, ErrorCode


class PromptMessage(BaseModel):
    role: str
    template: str


class PromptTemplate(BaseModel):
    name: str
    version: str
    description: str | None = None
    inputs: list[dict[str, Any]] = []
    model: dict[str, Any] = {}
    messages: list[PromptMessage]


class PromptRegistry:
    def __init__(self, root: Path):
        self.root = root
        self.templates: dict[str, PromptTemplate] = {}
        self.load_all()

    def load_all(self) -> None:
        if not self.root.exists():
            return
        for file in self.root.glob("*/*.yaml"):
            with file.open("r", encoding="utf-8") as fp:
                data = yaml.safe_load(fp)
            prompt = PromptTemplate.model_validate(data)
            key = f"{file.parent.name}/{file.stem}"
            self.templates[key] = prompt

    def render(self, key: str, **kwargs: Any) -> list[dict[str, str]]:
        if key not in self.templates:
            raise AgentError(ErrorCode.NOT_FOUND, f"Prompt 不存在: {key}")
        prompt = self.templates[key]
        for item in prompt.inputs:
            if item.get("required") and kwargs.get(item["name"]) is None:
                raise AgentError(ErrorCode.PARAM_INVALID, f"Prompt 参数缺失: {item['name']}")
        return [
            {"role": message.role, "content": Template(message.template).render(**kwargs)}
            for message in prompt.messages
        ]

    def model_meta(self, key: str) -> dict[str, Any]:
        if key not in self.templates:
            raise AgentError(ErrorCode.NOT_FOUND, f"Prompt 不存在: {key}")
        return self.templates[key].model
