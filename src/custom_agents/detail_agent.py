from agents import Agent
from models.curriculum import DetailedSyllabus

detail_agent = Agent(
    name="Detail Drafter",
    instructions=(
        "Expand an approved curriculum into a detailed syllabus. "
        "For each module, produce 4–8 actionable subtopics (bullets). Be specific; "
        "avoid fluff (no 'learn basics')."
    ),
    output_type=DetailedSyllabus
)
