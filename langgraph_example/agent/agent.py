from langgraph.graph import StateGraph
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, SystemMessage
from typing import TypedDict, Annotated, Sequence

#------------------- State -------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

workflow = StateGraph(AgentState) # Create a new graph, then add to it the state


#------------------ LLM Node -----------------
from langchain_google_genai import ChatGoogleGenerativeAI

def _get_model():
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
    model.bind_tools(all_tools)
    return model


system_prompt = "You are such a nice helpful bot"

def call_model(state):
    print('state before llm call :', state)
    messages = state["messages"]
    
    # add the state to the default system message
    system_message = SystemMessage(content=system_prompt)
    full_messages = [system_message] + messages
    
    model = _get_model()
    response = model.invoke(full_messages)
    print('llm response :', response)
    
    return {"messages": [response]}


#---------------- Tools Node ---------------

from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

@tool
def weather_tool() -> str:
    """Get the current weather."""
    return "Weather is 19°C and Partly Cloudy"

@tool
def calendar_tool() -> str:
    """Check your calendar for meetings on a specific date."""
    return "No meetings scheduled"

all_tools = [weather_tool, calendar_tool]
tool_node = ToolNode(all_tools)


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
        print('tool_calls :', last_message.tool_calls)
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