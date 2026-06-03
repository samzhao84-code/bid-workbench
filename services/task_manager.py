import json
import os
import uuid
from datetime import datetime
from typing import Optional

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
TASKS_DIR = os.path.join(DATA_DIR, "tasks")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

STATUSES = [
    "UPLOADED", "EXTRACTING", "PENDING_REVIEW",
    "EXPANDING", "TECH_REVIEW", "ADJUSTING",
    "GENERATING", "COMPLETED", "ERROR"
]


def ensure_dirs():
    for d in [DATA_DIR, TASKS_DIR, UPLOADS_DIR, OUTPUTS_DIR]:
        os.makedirs(d, exist_ok=True)


class Task:
    def __init__(
        self,
        task_id: str = None,
        status: str = "UPLOADED",
        project_name: str = "",
        tender_file_path: str = "",
        tender_text: str = "",
        requirements: list = None,
        expanded_solution: str = "",
        output_path: str = "",
        error: str = "",
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.project_name = project_name
        self.tender_file_path = tender_file_path
        self.tender_text = tender_text
        self.requirements = requirements or []
        self.expanded_solution = expanded_solution
        self.output_path = output_path
        self.error = error
        self.upload_dir = os.path.join(UPLOADS_DIR, self.task_id)
        self.output_dir = os.path.join(OUTPUTS_DIR, self.task_id)
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_name": self.project_name,
            "tender_file_path": self.tender_file_path,
            "tender_text": self.tender_text,
            "requirements": self.requirements,
            "expanded_solution": self.expanded_solution,
            "output_path": self.output_path,
            "error": self.error,
        }

    def save(self):
        self.updated_at = datetime.now().isoformat()
        filepath = os.path.join(TASKS_DIR, f"{self.task_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def update_status(self, status: str):
        self.status = status
        self.save()

    @staticmethod
    def load(task_id: str) -> Optional["Task"]:
        filepath = os.path.join(TASKS_DIR, f"{task_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        task = Task(task_id=data["task_id"])
        for k, v in data.items():
            setattr(task, k, v)
        task.upload_dir = os.path.join(UPLOADS_DIR, task.task_id)
        task.output_dir = os.path.join(OUTPUTS_DIR, task.task_id)
        os.makedirs(task.upload_dir, exist_ok=True)
        os.makedirs(task.output_dir, exist_ok=True)
        return task
