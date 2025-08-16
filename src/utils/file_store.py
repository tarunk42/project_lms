import json
from pathlib import Path
from .helpers import slugify

class FileContentStore:
    """
    Stores:
    - index: content/<course_id>/index.json
    - lessons: content/<course_id>/<mm>-<ss>-<slug>.md
    """
    def __init__(self, base: Path):
        self.base = base

    def course_dir(self, course_id: str) -> Path:
        p = self.base / course_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_index(self, course_id: str, index: dict) -> None:
        (self.course_dir(course_id) / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    def load_index(self, course_id: str) -> dict:
        return json.loads((self.course_dir(course_id) / "index.json").read_text(encoding="utf-8"))

    def lesson_path(self, course_id: str, m_idx: int, s_idx: int, title: str) -> Path:
        filename = f"{m_idx+1:02d}-{s_idx+1:02d}-{slugify(title)}.md"
        return self.course_dir(course_id) / filename

    def has_lesson(self, course_id: str, m_idx: int, s_idx: int, title: str) -> bool:
        return self.lesson_path(course_id, m_idx, s_idx, title).exists()

    def write_lesson(self, course_id: str, m_idx: int, s_idx: int, title: str, markdown: str) -> Path:
        p = self.lesson_path(course_id, m_idx, s_idx, title)
        p.write_text(markdown, encoding="utf-8")
        return p

    def read_lesson(self, course_id: str, m_idx: int, s_idx: int, title: str) -> str:
        return self.lesson_path(course_id, m_idx, s_idx, title).read_text(encoding="utf-8")
