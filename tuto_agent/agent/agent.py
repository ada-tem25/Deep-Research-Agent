import os
from langgraph.graph import StateGraph
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
load_dotenv()

#------------------- State -------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    total_tokens: int

workflow = StateGraph(AgentState) # Create a new graph, then add to it the state


#---------------- Tools Node ---------------

from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

@tool
def weather_tool() -> str:
    """Get the current weather."""
    print('- Weather tool called.')
    return "Weather is 19°C and Partly Cloudy"

@tool
def calendar_tool() -> str:
    """Check your calendar for meetings on a specific date."""
    print('- Calendar tool called.')
    return "No meetings scheduled"

all_tools = [weather_tool, calendar_tool]
tool_node = ToolNode(all_tools)


#------------------ LLM Node -----------------
from langchain_google_genai import ChatGoogleGenerativeAI


def _get_model():
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", api_key=os.getenv("GOOGLE_API_KEY"))
    model = model.bind_tools(all_tools)
    return model


system_prompt = "You are such a nice helpful bot"

def call_model(state):
    messages = state["messages"]
    
    # add the state to the default system message
    system_message = SystemMessage(content=system_prompt)
    full_messages = [system_message] + messages
    model = _get_model()
    print('> LLM Call.')

    response = model.invoke(full_messages)

    tokens_used = response.usage_metadata['total_tokens']
    new_total = state["total_tokens"] + tokens_used
    print(f"[TOKENS] this call = {tokens_used} | accumulated = {new_total}")
    return {"messages": [response], "total_tokens": new_total}


# --------------- Define Nodes -------------

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# entry point
workflow.set_entry_point("agent")


# ------------- Define Edges ------------

# connect tools back to agent
workflow.add_edge("tools", "agent")

from langgraph.graph import END

# define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # if there are no tool calls, then we finish
    if not last_message.tool_calls: 
        return "end"
    # if there is, we continue
    else:
        return "continue"

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)


# ------------ Compile Workflow -----------

graph = workflow.compile()


# ------------ Execute Code ---------------


if __name__ == "__main__":
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path='./agent_graph.png')

    messages = [HumanMessage(content="What's the weather today?")]
    result = graph.invoke({"messages": messages, "total_tokens": 0})

    for m in result["messages"]:
        m.pretty_print()
