import os
from datetime import date

import numexpr
import wikipedia
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")

llm = init_chat_model(
    "openai/gpt-oss-120b",
    model_provider="openai",
    base_url="https://openrouter.ai/api/v1",
    temperature=0.6,
    # Only use OpenRouter providers that support tool calling
    extra_body={"provider": {"require_parameters": True}},
)


# Wikipedia blocks requests that don't say who is calling (a "User-Agent").
# The wikipedia package sends a generic one, so we set our own.
wikipedia.set_user_agent("WikiCalcAgent/1.0 (https://samrandevs.com)")

# Tool 1: Wikipedia (ready-made tool from langchain_community)
wikipedia_tool = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000)
)


# Tool 2: calculator (replaces the old "llm-math" tool)
@tool
def calculator(expression: str) -> str:
    """Calculate a math expression like '2026 - 1971' or '25 * 4 / 2'. Input must be plain math only."""
    try:
        return str(numexpr.evaluate(expression).item())
    except Exception as e:
        return f"Could not calculate: {e}"


agent = create_agent(
    model=llm,
    tools=[wikipedia_tool, calculator],
    system_prompt=(
        f"You are a helpful assistant. Today's date is {date.today():%B %d, %Y}. "
        "Use the wikipedia tool for facts about people, places and events. "
        "Use the calculator tool for any math. Keep answers short."
    ),
)


def ask_agent(question, verbose=False):
    """Run the agent. Returns (final_answer, steps).

    verbose=True prints every step in the terminal as it happens,
    like the old `verbose=True` in initialize_agent.
    """
    steps = []
    final_answer = ""

    # stream() gives us the agent's state after every step, instead of only the end result
    for state in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        msg = state["messages"][-1]
        if verbose:
            msg.pretty_print()
        steps.append(msg)
        final_answer = msg.content

    return final_answer, steps