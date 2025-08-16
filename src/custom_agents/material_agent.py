from agents import Agent

material_agent = Agent(
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
        "$$\\text{Your math here}$$\n\n, for example:\n"
        "This sentence uses `$` delimiters to show math inline: $\\sqrt{3x-1}+(1+x)^2$\n"
        "## Checks for Understanding\n- <questions>\n\n"
        "## Practice\n- <tasks>\n\n"
        "Return ONLY valid Markdown. Do NOT include any explanations outside the Markdown."
    )
)
