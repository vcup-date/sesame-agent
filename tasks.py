"""sesame agent — tasks.py — a live todo list the agent maintains (Claude-Code style).

One tool, `plan`, replaces the WHOLE list each call (like Claude Code's TodoWrite),
so the model keeps a single source of truth for what it is doing on a multi-step job.
The rendered list comes back as the tool result, so it prints in the transcript as the
work proceeds, and a header line summarises progress ("2/5 done · doing: …").

Pure state with no I/O, so it is trivially testable and can be persisted with the
session next to the goal and loop.
"""

STATUSES = ("pending", "in_progress", "completed")
MARK = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}


class TaskList:
    def __init__(self, items=None):
        self.items = []          # list of {"subject": str, "status": str}
        if items:
            self.set(items)

    def set(self, items):
        """Replace the whole list. Accepts dicts ({subject|content, status}) or bare
        strings; unknown statuses fall back to pending. Returns self."""
        cleaned = []
        for it in items or []:
            if isinstance(it, dict):
                subject = str(it.get("subject") or it.get("content") or "").strip()
                status = it.get("status", "pending")
            else:
                subject = str(it).strip()
                status = "pending"
            if not subject:
                continue
            if status not in STATUSES:
                status = "pending"
            cleaned.append({"subject": subject, "status": status})
        self.items = cleaned
        return self

    def progress(self):
        """(done, total, current_subject) — current is the first in_progress task."""
        done = sum(1 for i in self.items if i["status"] == "completed")
        current = next((i["subject"] for i in self.items if i["status"] == "in_progress"), "")
        return done, len(self.items), current

    def render(self):
        if not self.items:
            return "(no tasks)"
        done, total, current = self.progress()
        head = f"Plan — {done}/{total} done"
        if current:
            head += f" · doing: {current}"
        lines = [head] + [f"  {MARK[i['status']]} {i['subject']}" for i in self.items]
        return "\n".join(lines)

    def to_dict(self):
        return {"items": self.items}

    @classmethod
    def from_dict(cls, d):
        return cls((d or {}).get("items") or [])


def make_task_tools(tasklist, on_change=None):
    """One `plan` tool bound to a TaskList. on_change(tasklist) fires after each update
    so a UI can repaint a progress header."""
    def _plan(inp):
        tasklist.set(inp.get("tasks") or [])
        if on_change:
            on_change(tasklist)
        return {"ok": True, "content": tasklist.render()}

    plan = {
        "name": "plan",
        "read_only": False,
        "description": (
            "Maintain a short todo list for a multi-step task (Claude-Code style). Call it "
            "with the FULL list every time, updating statuses as you go: keep exactly one task "
            "in_progress while you work it and mark it completed the moment it is done. Keep "
            "subjects concise and outcome-focused. Use this for non-trivial multi-step work so "
            "the user can watch progress; skip it for simple one-step requests."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "Concise task description"},
                            "status": {"type": "string", "enum": list(STATUSES)},
                        },
                        "required": ["subject"],
                    },
                }
            },
            "required": ["tasks"],
        },
        "execute": _plan,
    }
    return [plan]
