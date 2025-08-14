from __future__ import annotations
import os, requests, textwrap, html, re
from typing import List, Dict
from dotenv import load_dotenv
import pprint

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("No 'OPENAI_API_KEY' found in the environment variables")

from rich.console import Console
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

console.print("[cyan bold]Hello Learner[/cyan bold]")


from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime


from pydantic import BaseModel, Field, AliasChoices
from agents import Agent, Runner, RunConfig, ModelSettings
import nest_asyncio, asyncio

CONTENT_DIR = Path("content")
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

class Module(BaseModel):
    name: str
    lessons: List[str] = Field(..., description="3–7 concise lesson titles in logical order")


class Curriculum(BaseModel):
    topic: str
    level: str = "beginner"
    goal: Optional[str] = None
    modules: List[Module]


class Review(BaseModel):
    approved: bool
    issues: List[str] = []
    revision_instructions: str = ""

class DetailedTopic(BaseModel):
    title: str
    subtopics: List[str] = Field(..., validation_alias=AliasChoices("subtopics", "subtopic"))

class DetailedSyllabus(BaseModel):
    topic: str
    outline: List[DetailedTopic]

# Utility functions
def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def sha256_text(s: str) -> str:
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def short(h: str, n: int = 8) -> str:
    """Shorten a hash to n characters."""
    return h[:n]

# File based content storage
class FileContentStore:
    """
    Stores:
    - index: content/<course_id>/index.json
    - lessons: content/<course_id>/<mm>-<ss>-<slug>.md
    """
    def __init__(self, base: Path = CONTENT_DIR):
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


# Orchestration Class
@dataclass
class Orchestrator:
    model: str = "gpt-4o"
    temperature: float = 0.2

    def __post_init__(self):
        self.curriculum_agent = Agent(
            name="Curriculum Planner",
            instructions=(
                "You create tight, pragmatic learning curricula. "
                "Given a topic, level, goal, and any user change requests, "
                "produce a short curriculum with 3–6 modules. Keep lesson titles concise. "
                "Prefer fundamentals first, then practice."
            ),
            output_type=Curriculum
        )

        self.reviewer_agent = Agent(
            name="Curriculum Reviewer",
            instructions=(
                "You critically review a curriculum for prerequisite order, scope creep, "
                "jargon, and uneven load. If fixes are needed, set approved=false and write "
                "a single, crisp set of revision instructions."
            ),
            output_type=Review,
        )

        self.detail_agent = Agent(
            name="Detail Drafter",
            instructions=(
                "Expand an approved curriculum into a detailed syllabus. "
                "For each module, produce 4–8 actionable subtopics (bullets). Be specific; "
                "avoid fluff (no 'learn basics')."
            ),
            output_type=DetailedSyllabus,
        )

        # Pure markdown output (no schema) — single responsibility: produce lesson material for one subtopic.
        self.material_agent = Agent(
            name="Material Generator",
            instructions=(
                "You generate COMPLETE, self-contained STUDY MATERIAL in STRICT MARKDOWN ONLY for a single subtopic. "
                "Use this exact template:\n\n"
                "# <Subtopic Title>\n"
                "**What you'll learn:** <3–5 bullets>\n"
                "**Prerequisites:** <bullets if any>\n\n"
                "## Concepts\n- <bullets>\n\n"
                "## Walkthrough\n1. <step-by-step>\n\n"
                "## Code\n```python\n# if relevant, provide runnable examples\n```\n\n" 
                "## If math is involved, use LaTeX syntax:\n"
                "$$\\text{Your math here}$$\n\n, for example:\nThis sentence uses `$` delimiters to show math inline: $\sqrt{3x-1}+(1+x)^2$"
                "## Checks for Understanding\n- <questions>\n\n"
                "## Practice\n- <tasks>\n\n"
                "Return ONLY valid Markdown. Do NOT include any explanations outside the Markdown."
            ),
            # No output_type => returns plain text
        )

        self._run_config = RunConfig(
            model=self.model,
            model_settings=ModelSettings(temperature=self.temperature),
            workflow_name="LearningPlatform_MVP",
        )

        self.store = FileContentStore()

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
        console.print(Panel(f"[bold cyan]Review Prompt: [/bold cyan] \n[dim] {prompt} [/dim]")) # check review prompt
        res = Runner.run_sync(self.reviewer_agent, prompt, run_config=self._run_config)
        return res.final_output

    # revise loop
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


    def draft_details(self, curriculum: Curriculum) -> DetailedSyllabus:
        prompt = (
            "Expand this approved curriculum into a detailed syllabus with topics and bulleted subtopics.\n\n"
            f"{curriculum.model_dump_json(indent=2)}\n"
            "Return a DetailedSyllabus."
        )
        res = Runner.run_sync(self.detail_agent, prompt, run_config=self._run_config)
        return res.final_output  # -> DetailedSyllabus

    # ---- Material Generation ----

    def _prompt_hash(self) -> str:
        # Hash the material agent instruction + model choices to trigger regen when template/model changes
        basis = f"{self.material_agent.instructions}|{self.model}|{self.temperature}"
        return sha256_text(basis)

    def _syllabus_hash(self, syllabus: DetailedSyllabus) -> str:
        return sha256_text(syllabus.model_dump_json())

    def _course_id(self, topic: str, syllabus_hash: str) -> str:
        return f"{slugify(topic)}-{short(syllabus_hash)}"

    def save_course(self, curriculum: Curriculum, syllabus: DetailedSyllabus) -> str:
        s_hash = self._syllabus_hash(syllabus)
        p_hash = self._prompt_hash()
        course_id = self._course_id(curriculum.topic, s_hash)
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
        return res.final_output  # plain markdown string
    
    def get_or_build_lesson(
        self,
        course_id: str,
        module_idx: int,
        subtopic_idx: int,
    ) -> Tuple[str, str]:
        """Returns (title, markdown). Builds once and caches to disk."""
        index = self.store.load_index(course_id)
        syllabus = DetailedSyllabus.model_validate(index["syllabus"])
        module = syllabus.outline[module_idx]
        title = module.subtopics[subtopic_idx]

        if not self.store.has_lesson(course_id, module_idx, subtopic_idx, title):
            md = self.generate_material_markdown(syllabus, module_idx, subtopic_idx)
            self.store.write_lesson(course_id, module_idx, subtopic_idx, title, md)
        else:
            md = self.store.read_lesson(course_id, module_idx, subtopic_idx, title)

        return title, md

    # ---- Public API ----
    # ---- Public API ----
    def orchestrate(
        self,
        topic: str,
        level: str = "beginner",
        goal: Optional[str] = None,
        get_user_feedback: Optional[Callable[[Curriculum, Review], Optional[str]]] = None,
    ) -> DetailedSyllabus:
        draft = self.plan_curriculum(topic, level, goal)
        approved = self.revise_until_approved(draft, get_user_feedback=get_user_feedback)
        return self.draft_details(approved)



    # ---- Utils ----

    @staticmethod
    def _merge_changes(reviewer_instr: str, user_change: Optional[str]) -> str:
        parts = []
        if reviewer_instr and reviewer_instr.strip():
            parts.append(f"Reviewer: {reviewer_instr.strip()}")
        if user_change and user_change.strip():
            parts.append(f"User: {user_change.strip()}")
        return "\n".join(parts) if parts else "No changes—tighten clarity and ordering."


# --- CLI (extended) ---

console = Console()

def _cli_feedback(curriculum: Curriculum, review: Review) -> Optional[str]:
    console.rule("[bold]REVIEW[/bold]")
    console.print(f"[bold]Approved:[/bold] {review.approved}")
    if review.issues:
        table = Table(title="Issues")
        table.add_column("#", justify="right")
        table.add_column("Issue")
        for i, iss in enumerate(review.issues, 1):
            table.add_row(str(i), iss)
        console.print(table)
    if review.revision_instructions:
        console.print(f"[bold]Reviewer instructions:[/bold] {review.revision_instructions}")

    ans = Prompt.ask(
        "Accept reviewer’s changes? ([y]=accept & continue, n=add your own, a=approve anyway)",
        choices=["y","n","a",""], default="y"
    ).lower()

    if ans == "a":
        # Force-approve by returning no change; loop will re-check approval next pass.
        return None
    if ans == "y" or ans == "":
        return review.revision_instructions
    if ans == "n":
        user = Prompt.ask("Describe your change request (1–2 sentences)", default="")
        return user or review.revision_instructions

if __name__ == "__main__":
    console.print("[bold]=== Learning Platform Orchestrator (MVP, Extended) ===[/bold]")
    topic = Prompt.ask("What do you want to learn?").strip()
    level = Prompt.ask("Level", choices=["beginner","intermediate","advanced"], default="beginner").strip()
    goal = Prompt.ask("Goal (optional)", default="").strip() or None

    orch = Orchestrator()

    # 1) First draft
    draft = orch.plan_curriculum(topic=topic, level=level, goal=goal)
    console.rule("[bold]INITIAL CURRICULUM DRAFT[/bold]")
    console.print(Markdown(f"```json\n{draft.model_dump_json(indent=2)}\n```"))

    # 2) Review loop (human-in-the-loop)
    approved = orch.revise_until_approved(draft, get_user_feedback=_cli_feedback)
    console.rule("[bold]APPROVED CURRICULUM[/bold]")
    console.print(Markdown(f"```json\n{approved.model_dump_json(indent=2)}\n```"))

    # 3) Detailed syllabus
    detailed = orch.draft_details(approved)
    console.rule("[bold]DETAILED SYLLABUS[/bold]")

    # Pretty summary table
    table = Table(title="Modules & Subtopics")
    table.add_column("Module #", justify="right")
    table.add_column("Module Title")
    table.add_column("Subtopics (count)", justify="right")
    for i, mod in enumerate(detailed.outline, 1):
        subs = getattr(mod, "subtopics", getattr(mod, "subtopic", []))
        table.add_row(f"{i:02d}", mod.title, str(len(subs)))

    console.print(table)

    # Raw JSON (optional)
    console.print(Panel.fit(Markdown(f"```json\n{detailed.model_dump_json(indent=2)}\n```"), title="Detailed JSON"))

    # 4) Persist course (so materials can be generated/viewed later)
    course_id = orch.save_course(approved, detailed)
    console.print(f"[green]Saved course:[/green] [bold]{course_id}[/bold]  (stored under ./content/{course_id})")

    # 5) Quick actions for materials
    if Confirm.ask("Build all study materials now?", default=False):
        index = orch.store.load_index(course_id)
        syllabus = DetailedSyllabus.model_validate(index["syllabus"])
        total = sum(len(m.subtopics) for m in syllabus.outline)
        done = 0
        for m_idx, mod in enumerate(syllabus.outline):
            for s_idx, _ in enumerate(mod.subtopics):
                title, _ = orch.get_or_build_lesson(course_id, m_idx, s_idx)
                done += 1
                console.print(f"[green]Built[/green] {done}/{total}: [bold]{mod.title}[/bold] → {title}")
        console.print("[bold green]All materials generated.[/bold green]")
    elif Confirm.ask("Open a subtopic now?", default=True):
        mm = int(Prompt.ask("Module number (mm, 1-based)"))
        ss = int(Prompt.ask("Subtopic number (ss, 1-based)"))
        title, md = orch.get_or_build_lesson(course_id, mm-1, ss-1)
        console.rule(f"[bold]{title}[/bold]")
        console.print(Markdown(md))
