from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List

from sqlalchemy.orm import Session

from ..db import models


class MemoryStore:
    """A simple task-scoped memory buffer with periodic compaction and inspection."""

    def __init__(
        self,
        db: Session,
        task_id: str,
        llm: object | None = None,
        compact_threshold: int = 5,
        log_task_events: bool = True,
    ):
        self.db = db
        self.task_id = task_id
        # LLM is optional; if provided it should mirror the async LLMClient API.
        self.llm = llm
        self.compact_threshold = compact_threshold
        self.log_task_events = log_task_events

    def _buffer_scope(self) -> str:
        return f"task:{self.task_id}:buffer"

    def _summary_scope(self) -> str:
        return f"task:{self.task_id}:summary"

    def _get_or_create_chunk(self, scope: str) -> models.MemoryChunk:
        chunk = (
            self.db.query(models.MemoryChunk)
            .filter(models.MemoryChunk.scope == scope)
            .order_by(models.MemoryChunk.last_updated.desc())
            .first()
        )
        if not chunk:
            chunk = models.MemoryChunk(
                user_id=self.task_id,
                scope=scope,
                summary="",
                embedding=None,
                last_updated=datetime.now(timezone.utc),
            )
            self.db.add(chunk)
            self.db.commit()
            self.db.refresh(chunk)
        return chunk

    def add_event(self, text: str) -> None:
        """Append an event to the buffer and compact if needed."""

        buffer = self._get_or_create_chunk(self._buffer_scope())
        combined = f"{buffer.summary}\n{text}".strip()
        buffer.summary = combined
        buffer.last_updated = datetime.now(timezone.utc)
        self.db.add(buffer)
        self.db.commit()
        self._maybe_compact(buffer)
        if self.log_task_events:
            event = models.TaskEvent(
                task_id=self.task_id,
                session_type="memory",
                agent_role="Memory",
                event_type="note",
                payload={"text": text},
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(event)
            self.db.commit()

    def _maybe_compact(self, buffer: models.MemoryChunk) -> None:
        events = [line for line in buffer.summary.splitlines() if line.strip()]
        if len(events) < self.compact_threshold:
            return

        summary_text = self._summarize(events)
        summary_chunk = self._get_or_create_chunk(self._summary_scope())
        summary_chunk.summary = summary_text
        summary_chunk.last_updated = datetime.now(timezone.utc)
        self.db.add(summary_chunk)

        buffer.summary = ""
        buffer.last_updated = datetime.now(timezone.utc)
        self.db.commit()

        if self.log_task_events:
            compaction_event = models.TaskEvent(
                task_id=self.task_id,
                session_type="memory",
                agent_role="Memory",
                event_type="compact",
                payload={"events_compacted": len(events), "summary": summary_text},
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(compaction_event)
            self.db.commit()

    def _summarize(self, events: Iterable[str]) -> str:
        # If an LLM is provided, we could call it to summarize. For now, keep it synchronous
        # and deterministic for tests by joining events.
        return " | ".join(events)

    def query(self, k: int = 3) -> list[str]:
        summaries = (
            self.db.query(models.MemoryChunk)
            .filter(models.MemoryChunk.scope == self._summary_scope())
            .order_by(models.MemoryChunk.last_updated.desc())
            .limit(k)
            .all()
        )
        return [s.summary for s in summaries if s.summary]

    def buffer_events(self) -> List[str]:
        """Return buffered, un-compacted events for inspection by the UI."""

        buffer = self._get_or_create_chunk(self._buffer_scope())
        return [line for line in buffer.summary.splitlines() if line.strip()]

    def summaries(self, k: int = 5) -> List[str]:
        """Return recent summary chunks (most recent first)."""

        return self.query(k=k)
