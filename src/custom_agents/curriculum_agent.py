from agents import Agent
from src.models.curriculum import Curriculum

curriculum_agent = Agent(
    name="Curriculum Planner",
    instructions=(
        "You create tight, pragmatic learning curricula. "
        "Given a topic, level, goal, and any user change requests, "
        "produce a short curriculum with 3–6 modules. Keep lesson titles concise. "
        "Prefer fundamentals first, then practice."
    ),
    output_type=Curriculum
)
