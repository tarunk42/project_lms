from agents import Agent
from models.curriculum import Review

reviewer_agent = Agent(
    name="Curriculum Reviewer",
    instructions=(
        "You critically review a curriculum for prerequisite order, scope creep, "
        "jargon, and uneven load. If fixes are needed, set approved=false and write "
        "a single, crisp set of revision instructions."
    ),
    output_type=Review
)
