from src.tools.web_search_tool import brave_web_search
from agents import Agent, Runner
import asyncio

search_agent = Agent(
    name="Web Search",
    instructions=(
        "You perform web searches to find information. "
        "When the user provides a query, CALL the web_search_tool. "
        "Then return a structured output of the search results."
        "Title - {title}\n"
        "URL - {url}\n"
        "Snippet - {snippet}\n"
    ),
    tools=[brave_web_search],
)

async def main():
    user_query = "What is the capital of France?"
    result = await Runner.run(search_agent, user_query)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())