from agents import Agent, Runner, function_tool

prompt = (
    "You are a helpful study assistant."
    "Your task is to converse with the user to help them understand a topic or answer their question related to the course."
)

study_assistant_agent = Agent(
    name="Study Assistant",
    instructions=prompt,
    tools=[]
)