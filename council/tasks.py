"""Background task manager using ThreadPoolExecutor.

Runs enrichment and other long-running operations in background threads
so the Flask request cycle is not blocked.
"""

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    """Mutable progress object shared with the background task function."""

    status: TaskStatus = TaskStatus.PENDING
    message: str = "Waiting..."
    progress: float = 0.0  # 0.0 to 1.0
    substeps: list[dict] = field(default_factory=list)
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "message": self.message,
            "progress": round(self.progress, 2),
            "substeps": self.substeps,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """Singleton background task manager.

    Uses ThreadPoolExecutor because Flask is synchronous and LLM calls
    release the GIL during I/O wait.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_workers: int = 3):
        if self._initialized:
            return
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskProgress] = {}
        self._initialized = True

    def submit(
        self,
        task_fn: Callable[..., Any],
        task_id: str | None = None,
        **kwargs,
    ) -> str:
        """Run *task_fn* in a background thread.

        The function receives a ``progress`` keyword argument it can use
        to report progress back to the caller.

        Returns the task ID (auto-generated if not provided).
        """
        if task_id is None:
            task_id = str(uuid.uuid4())[:8]

        progress = TaskProgress(status=TaskStatus.RUNNING, message="Starting...")
        self._tasks[task_id] = progress

        def _wrapper():
            try:
                result = task_fn(progress=progress, **kwargs)
                progress.result = result
                progress.status = TaskStatus.COMPLETED
                progress.progress = 1.0
                if not progress.message or progress.message == "Starting...":
                    progress.message = "Complete"
            except Exception as exc:
                progress.status = TaskStatus.FAILED
                progress.error = str(exc)
                progress.message = f"Failed: {exc}"

        self._executor.submit(_wrapper)
        return task_id

    def get_status(self, task_id: str) -> TaskProgress | None:
        return self._tasks.get(task_id)

    def list_tasks(self) -> dict[str, dict]:
        return {tid: tp.to_dict() for tid, tp in self._tasks.items()}


def get_task_manager() -> TaskManager:
    """Return the singleton TaskManager."""
    return TaskManager()
