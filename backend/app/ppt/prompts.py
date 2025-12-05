from __future__ import annotations

import re
from pathlib import Path


class PromptNotebook:
    """Store prompts in Markdown so they can be iterated, read, and diffed."""

    def __init__(self, root: Path, topic: str, session_id: str | None = None, max_history: int = 10):
        self.root = Path(root)
        self.topic = topic
        self.session_id = session_id or "default"
        self.max_history = max_history
        self.topic_dir = self.root / "ppt" / self._slugify(topic) / self._slugify(self.session_id)
        self.topic_dir.mkdir(parents=True, exist_ok=True)

    def save_prompt(self, stage: str, prompt: str) -> Path:
        """Append a new iteration of a prompt for a given stage as Markdown."""

        path = self.prompt_path(stage)
        header = f"# {stage.title()} Prompt Notebook"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            iteration = self._next_iteration(existing)
            content = f"{existing.rstrip()}\n\n{self._iteration_block(iteration, prompt)}"
        else:
            iteration = 1
            content = f"{header}\n\n{self._iteration_block(iteration, prompt)}"

        trimmed = self._trim_iterations(content, self.max_history)
        path.write_text(trimmed, encoding="utf-8")
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
    def _iteration_block(iteration: int, prompt: str) -> str:
        return f"## Iteration {iteration}\n\n{prompt.strip()}\n"

    @staticmethod
    def _trim_iterations(content: str, limit: int) -> str:
        """Keep only the latest `limit` iterations to avoid unbounded growth."""
        if limit <= 0:
            return content

        first = re.search(r"## Iteration \d+", content)
        if not first:
            return content

        header = content[: first.start()].strip()
        body = content[first.start():]
        pattern = re.compile(r"## Iteration \d+\n(?:[\s\S]*?)(?=\n## Iteration \d+|\Z)", re.MULTILINE)
        iterations = pattern.findall(body)

        kept = iterations[-limit:] if len(iterations) > limit else iterations

        pieces = [header] if header else []
        pieces.extend(kept)
        return "\n\n".join(piece.rstrip() for piece in pieces if piece).rstrip() + "\n"

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\-]+", "-", value.strip().lower()).strip("-")
        return cleaned or "untitled"
