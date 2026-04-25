from __future__ import annotations

import logging

from litqip.constants import MAX_TODO_ITEMS

logger = logging.getLogger("litqip.todo")


class TodoItem:
    content: str
    status: str
    activeForm: str

    def __init__(self, content: str, status: str, activeForm: str) -> None:
        self.content = content
        self.status = status
        self.activeForm = activeForm

    def to_dict(self) -> dict[str, str]:
        return {"content": self.content, "status": self.status, "activeForm": self.activeForm}


class TodoManager:
    def __init__(self) -> None:
        self._items: list[TodoItem] = []

    def update(self, items: list[dict[str, Any]]) -> str:
        validated = []
        in_progress_count = 0
        for i, item in enumerate(items):
            content = str(item.get("content", "")).strip()
            status = str(item.get("status", "pending")).lower()
            active = str(item.get("activeForm", "")).strip()
            if not content:
                raise ValueError(f"Item {i}: content required")
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Item {i}: invalid status '{status}'")
            if not active:
                raise ValueError(f"Item {i}: activeForm required")
            if status == "in_progress":
                in_progress_count += 1
            validated.append({"content": content, "status": status, "activeForm": active})
        if len(validated) > MAX_TODO_ITEMS:
            raise ValueError("Max 20 todos")
        if in_progress_count > 1:
            raise ValueError("Only one in_progress allowed")
        self._items = [TodoItem(**v) for v in validated]
        logger.info("todos updated: %d items", len(self._items))
        return self.render()

    def render(self) -> str:
        if not self._items:
            return "No todos."
        lines = []
        for item in self._items:
            marker = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}.get(item.status, "[?]")
            suffix = f" <- {item.activeForm}" if item.status == "in_progress" else ""
            lines.append(f"{marker} {item.content}{suffix}")
        done = sum(1 for t in self._items if t.status == "completed")
        lines.append(f"\n({done}/{len(self._items)} completed)")
        return "\n".join(lines)

    def has_open_items(self) -> bool:
        return any(item.status != "completed" for item in self._items)

    def add(self, content: str, activeForm: str = "") -> str:
        """Add a single todo item."""
        if not activeForm:
            activeForm = content
        self._items.append(TodoItem(content=content, status="pending", activeForm=activeForm))
        return self.render()

    def complete(self, index: int) -> str:
        """Mark item at index as completed."""
        if 0 <= index < len(self._items):
            self._items[index].status = "completed"
        return self.render()

    def remove(self, index: int) -> str:
        """Remove item at index."""
        if 0 <= index < len(self._items):
            self._items.pop(index)
        return self.render()

    def list_items(self) -> list[TodoItem]:
        return list(self._items)


# Global instance
todo = TodoManager()
