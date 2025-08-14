import os
from typing import List, Optional
from pydantic import BaseModel, Field
from agents import Agent, Runner, SQLiteSession

# ---------- Shared structured payloads ----------
class TaskResult(BaseModel):
    task_name: str
    summary: str
    artifacts: List[str] = Field(default_factory=list)  # could be links/ids/notes

# ---------- Specialists ----------
researcher = Agent(
    name="Researcher",
    handoff_description="Find facts and produce a concise summary.",
    instructions=(
        "You perform factual research and return a short bullet summary.\n"
        "When done, call `transfer_to_User` with a TaskResult: "
        "task_name='research', summary=<bullets>, artifacts=<sources/notes>."
    ),
)

writer = Agent(
    name="Writer",
    handoff_description="Turn bullets into a crisp, user-facing answer.",
    instructions=(
        "You take research bullets (if provided) and write a clear answer.\n"
        "When done, call `transfer_to_User` with a TaskResult: "
        "task_name='writing', summary=<short synopsis>, artifacts=<outline/notes>."
    ),
)

# IMPORTANT: enable two-way by allowing specialists to hand back to User
# We attach the User agent later, after it's defined.

# ---------- User/Concierge agent ----------
# This is the single agent that always faces the user.
# It decides who to delegate to, then receives results back and continues the convo.
class UserDecision(BaseModel):
    delegate: Optional[str] = Field(
        description="One of ['Researcher','Writer'] or null to handle directly."
    )
    rationale: str

User = Agent(
    name="User",
    instructions=(
        "You are the main conversational agent. Talk to the user naturally.\n"
        "Decide whether to delegate to Researcher (for fact-gathering) or Writer "
        "(for polished prose). If delegation is needed, use a handoff.\n"
        "When a specialist hands results back, summarize what was done, show key "
        "outputs, ask the user if they want changes or to proceed."
    ),
    # Let the model decide to hand off to either specialist:
    handoffs=[researcher, writer],
)

# Now complete the circle: give specialists the ability to return to User
researcher.handoffs = [User]  # two-way
writer.handoffs = [User]      # two-way

# (Optional) You can constrain routing with a small decision schema:
router = Agent(
    name="Router",
    instructions=(
        "Given the user's latest message, decide whether User should handle it "
        "directly or delegate first. If delegation is needed, hand off to User "
        "and rely on User to delegate to a specialist."
    ),
    handoffs=[User],
    output_type=UserDecision,
)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")

    print("Two-way handoff demo. Type 'quit' to exit.")
    session = SQLiteSession("two_way_demo")

    while True:
        user_msg = input("\nYou: ").strip()
        if user_msg.lower() in {"quit", "exit"}:
            break

        # Start every turn at the User agent (or use router first if you prefer)
        result = Runner.run_sync(User, user_msg, session=session)
        print(f"\nAssistant:\n{result.final_output}")

        # The SDK preserves history; specialists can hand back to User next turn.
        # No extra code needed—just keep looping.
        # If you wanted streaming, swap to Runner.run_streamed.
        
if __name__ == "__main__":
    main()
