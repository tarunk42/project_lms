import sys
import os
import asyncio
import nest_asyncio

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Add the src directory to PYTHONPATH dynamically
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from src import Orchestrator

console = Console()

def _cli_feedback(curriculum, review):
    console.rule("[bold]REVIEW[/bold]")
    console.print(f"[bold]Approved:[/bold] {review.approved}")
    if review.issues:
        table = Table(title="Issues")
        table.add_column("#", justify="right")
        table.add_column("Issue")
        for i, issue in enumerate(review.issues, 1):
            table.add_row(str(i), issue)
        console.print(table)
    if review.revision_instructions:
        console.print(f"[bold]Reviewer instructions:[/bold] {review.revision_instructions}")

    ans = Prompt.ask(
        "Accept reviewer’s changes? ([y]=accept & continue, n=add your own, a=approve anyway)",
        choices=["y", "n", "a", ""],
        default="y",
    ).lower()

    if ans == "a":
        return None  # Force-approve by returning no change
    if ans in ["y", ""]:
        return review.revision_instructions
    if ans == "n":
        user_change = Prompt.ask("Describe your change request (1–2 sentences)", default="")
        return user_change or review.revision_instructions

async def build_materials_concurrent(orch, course_id, detailed):
    """Build materials concurrently with progress updates"""
    console.print("[bold yellow]Building materials concurrently...[/bold yellow]")
    
    total = sum(len(m.subtopics) for m in detailed.outline)
    console.print(f"📊 Building {total} lessons across {len(detailed.outline)} modules")
    
    # Get concurrency setting from user
    concurrency = int(Prompt.ask("Concurrency level (1-16)", default="6"))
    
    # Use the concurrent builder
    result = await orch.build_all_materials_concurrent(course_id, concurrency=concurrency)
    
    # Show results
    console.print(f"[bold green]✅ Build completed![/bold green]")
    console.print(f"Total lessons: {result['total']}")
    console.print(f"Successfully built: {result['completed']}")
    if result['failures']:
        console.print(f"[bold red]Failures: {len(result['failures'])}[/bold red]")
        for failure in result['failures']:
            console.print(f"  ❌ {failure}")
    else:
        console.print("[bold green]No failures![/bold green]")

async def main():
    console.clear()
    console.print(Panel("[bold bright_magenta]=== Step 1: Welcome User ===[/bold bright_magenta]"))
    console.print("[bold]=== Learning Platform Orchestrator (MVP, Extended) ===[/bold]")
    topic = Prompt.ask("What do you want to learn?").strip()
    level = Prompt.ask("Level", choices=["beginner", "intermediate", "advanced"], default="beginner").strip()
    goal = Prompt.ask("Goal (optional)", default="").strip() or None

    orch = Orchestrator()

    
    # 1) First draft
    console.print(Panel("[bold bright_magenta]=== Step 2: Curriculum ===[/bold bright_magenta]"))
    draft = orch.plan_curriculum(topic=topic, level=level, goal=goal)
    console.rule("[bold]INITIAL CURRICULUM DRAFT[/bold]")
    console.print(Markdown(f"```json\n{draft.model_dump_json(indent=2)}\n```"))

    # 2) Review loop (human-in-the-loop)
    console.print(Panel("[bold bright_magenta]=== Step 3: Review Loop ===[/bold bright_magenta]"))
    approved = orch.revise_until_approved(draft, get_user_feedback=_cli_feedback)
    console.rule("[bold]APPROVED CURRICULUM[/bold]")
    console.print(Markdown(f"```json\n{approved.model_dump_json(indent=2)}\n```"))

    # 3) Detailed syllabus
    console.print(Panel("[bold bright_magenta]=== Step 4: Detailed Syllabus ===[/bold bright_magenta]"))
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
    console.print(Panel("[bold bright_magenta]=== Step 5: Save Course ===[/bold bright_magenta]"))
    course_id = orch.save_course(approved, detailed)
    console.print(f"[green]Saved course:[/green] [bold]{course_id}[/bold]  (stored under ./content/{course_id})")

    # 5) Quick actions for materials
    console.print(Panel("[bold bright_magenta]=== Step 6: Quick Actions ===[/bold bright_magenta]"))
    if Confirm.ask("Build all study materials now?", default=False):
        # Use async concurrent building
        await build_materials_concurrent(orch, course_id, detailed)
    elif Confirm.ask("Open a subtopic now?", default=True):
        mm = int(Prompt.ask("Module number (mm, 1-based)"))
        ss = int(Prompt.ask("Subtopic number (ss, 1-based)"))
        title, md = orch.get_or_build_lesson(course_id, mm - 1, ss - 1)
        console.rule(f"[bold]{title}[/bold]")
        console.print(Markdown(md))

if __name__ == "__main__":
    asyncio.run(main())