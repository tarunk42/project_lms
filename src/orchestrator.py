from dataclasses import dataclass
from typing import Callable, Optional, Tuple
from models.curriculum import Curriculum, Review, DetailedSyllabus
from utils.file_store import FileContentStore
from utils.helpers import slugify, sha256_text, short
from custom_agents.curriculum_agent import curriculum_agent
from custom_agents.reviewer_agent import reviewer_agent
from custom_agents.detail_agent import detail_agent
from custom_agents.material_agent import material_agent
from agents import Runner, RunConfig, ModelSettings
from datetime import datetime
from pathlib import Path

# Initialize CONTENT_DIR properly
CONTENT_DIR = Path("content")
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Orchestrator:
    model: str = "gpt-4o"
    temperature: float = 0.2

    def __post_init__(self):
        self.curriculum_agent = curriculum_agent
        self.reviewer_agent = reviewer_agent
        self.detail_agent = detail_agent
        self.material_agent = material_agent

        self._run_config = RunConfig(
            model=self.model,
            model_settings=ModelSettings(temperature=self.temperature),
            workflow_name="LearningPlatform_MVP",
        )

        self.store = FileContentStore(base=CONTENT_DIR)

    def plan_curriculum(
        self,
        topic: str,
        level: str = "beginner",
        goal: Optional[str] = None,
        change_request: Optional[str] = None,
    ) -> Curriculum:
        prompt = (
            f"Topic: {topic}\nLevel: {level}\nGoal: {goal or 'Not specified'}\n"
            f"Change request (if any): {change_request or 'None'}\n"
            "Return a Curriculum object."
        )
        res = Runner.run_sync(self.curriculum_agent, prompt, run_config=self._run_config)
        return res.final_output

    def review(self, curriculum: Curriculum) -> Review:
        prompt = (
            "Review the following curriculum. Approve only if it is clear, ordered, "
            "balanced, and free of jargon.\n\n"
            f"{curriculum.model_dump_json(indent=2)}\n"
            "Return a Review object."
        )
        res = Runner.run_sync(self.reviewer_agent, prompt, run_config=self._run_config)
        return res.final_output

    def draft_details(self, curriculum: Curriculum) -> DetailedSyllabus:
        prompt = (
            "Expand this approved curriculum into a detailed syllabus with topics and bulleted subtopics.\n\n"
            f"{curriculum.model_dump_json(indent=2)}\n"
            "Return a DetailedSyllabus."
        )
        res = Runner.run_sync(self.detail_agent, prompt, run_config=self._run_config)
        return res.final_output

    def generate_material_markdown(
        self,
        syllabus: DetailedSyllabus,
        module_idx: int,
        subtopic_idx: int,
    ) -> str:
        module = syllabus.outline[module_idx]
        subtopic = module.subtopics[subtopic_idx]
        prompt = (
            f"Generate complete study material for this subtopic in STRICT MARKDOWN ONLY.\n\n"
            f"Course Topic: {syllabus.topic}\n"
            f"Module: {module.title}\n"
            f"Subtopic: {subtopic}\n"
        )
        res = Runner.run_sync(self.material_agent, prompt, run_config=self._run_config)
        return res.final_output

    def save_course(self, curriculum: Curriculum, syllabus: DetailedSyllabus) -> str:
        s_hash = sha256_text(syllabus.model_dump_json())
        p_hash = sha256_text(self.material_agent.instructions)
        course_id = f"{slugify(curriculum.topic)}-{short(s_hash)}"
        index = {
            "course_id": course_id,
            "topic": curriculum.topic,
            "level": curriculum.level,
            "goal": curriculum.goal,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "syllabus_hash": s_hash,
            "prompt_hash": p_hash,
            "syllabus": syllabus.model_dump(mode="json"),
        }
        self.store.save_index(course_id, index)
        return course_id

    def revise_until_approved(
        self,
        initial: Curriculum,
        get_user_feedback: Optional[Callable[[Curriculum, Review], Optional[str]]] = None,
        max_loops: int = 1,
    ) -> Curriculum:
        """Deterministic loop: (plan -> review -> optional user change -> re-plan)"""
        curriculum = initial
        for _ in range(max_loops):
            review = self.review(curriculum)

            if review.approved:
                return curriculum

            # Merge reviewer instructions + (optional) user feedback into a single, crisp change request.
            user_change = get_user_feedback(curriculum, review) if get_user_feedback else None
            merged_change = self._merge_changes(review.revision_instructions, user_change)

            curriculum = self.plan_curriculum(
                topic=curriculum.topic,
                level=curriculum.level,
                goal=curriculum.goal,
                change_request=merged_change,
            )

        # Last resort: return latest even if not approved
        return curriculum

    @staticmethod
    def _merge_changes(reviewer_instr: str, user_change: Optional[str]) -> str:
        parts = []
        if reviewer_instr and reviewer_instr.strip():
            parts.append(f"Reviewer: {reviewer_instr.strip()}")
        if user_change and user_change.strip():
            parts.append(f"User: {user_change.strip()}")
        return "\n".join(parts) if parts else "No changes—tighten clarity and ordering."

    def get_or_build_lesson(
        self, course_id: str, module_idx: int, subtopic_idx: int
    ) -> Tuple[str, str]:
        """Retrieve or generate study material for a specific subtopic."""
        index = self.store.load_index(course_id)
        syllabus = DetailedSyllabus.model_validate(index["syllabus"])

        module = syllabus.outline[module_idx]
        subtopic = module.subtopics[subtopic_idx]
        lesson_id = f"{course_id}/{module_idx:02d}-{subtopic_idx:02d}-{slugify(subtopic)}"

        lesson_path = self.store.base / lesson_id
        if lesson_path.exists():
            return subtopic, lesson_path.read_text(encoding="utf-8")

        # Generate material if it doesn't exist
        material = self.generate_material_markdown(syllabus, module_idx, subtopic_idx)
        lesson_path.write_text(material, encoding="utf-8")
        return subtopic, material

    def _prompt_hash(self) -> str:
        # Hash the material agent instruction + model choices to trigger regen when template/model changes
        basis = f"{self.material_agent.instructions}|{self.model}|{self.temperature}"
        return sha256_text(basis)

    def _syllabus_hash(self, syllabus: DetailedSyllabus) -> str:
        return sha256_text(syllabus.model_dump_json())

    def _course_id(self, topic: str, syllabus_hash: str) -> str:
        return f"{slugify(topic)}-{short(syllabus_hash)}"
