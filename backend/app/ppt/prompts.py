from __future__ import annotations

import re
from pathlib import Path


class PromptNotebook:
    """Store prompts in Markdown so they can be iterated, read, and diffed."""

    def __init__(self, root: Path, topic: str):
        self.root = Path(root)
        self.topic = topic
        self.topic_dir = self.root / "ppt" / self._slugify(topic)
        self.topic_dir.mkdir(parents=True, exist_ok=True)

    def save_prompt(self, stage: str, prompt: str) -> Path:
        """Append a new iteration of a prompt for a given stage as Markdown."""

        path = self.prompt_path(stage)
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            iteration = self._next_iteration(existing)
            content = f"{existing}\n\n## Iteration {iteration}\n\n{prompt.strip()}\n"
        else:
            content = f"# {stage.title()} Prompt Notebook\n\n## Iteration 1\n\n{prompt.strip()}\n"
        path.write_text(content, encoding="utf-8")
        return path

    def read_prompt(self, stage: str) -> str | None:
        path = self.prompt_path(stage)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def prompt_path(self, stage: str) -> Path:
        return self.topic_dir / f"{stage}.md"

    @staticmethod
    def _next_iteration(existing: str) -> int:
        matches = re.findall(r"## Iteration (\d+)", existing)
        if not matches:
            return 1
        return max(int(match) for match in matches) + 1

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\-]+", "-", value.strip().lower()).strip("-")
        return cleaned or "untitled"
