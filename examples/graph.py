import os
from typing import Annotated, TypedDict, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from mkinf import hub as mh

# tools = mh.pull(["cyclotruc/gitingest"])
# tools = mh.pull(
#   ["tavily-ai/tavily-mcp"],
#   {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")})
#
tools = mh.pull(
	["ScrapeGraphAI/scrapegraphai"],
  {
    "SCRAPEGRAPH_LLM_MODEL": "openai/gpt-4o-mini",
    "SCRAPEGRAPH_LLM_API_KEY": os.getenv("OPENAI_API_KEY")
  }
)


system_prompt = "Be a helpful assistant."


# This is the default state same as "MessageState" TypedDict but allows us accessibility to custom keys
class GraphsState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    # Custom keys for additional data can be added here such as - conversation_id: str


graph = StateGraph(GraphsState)
tool_node = ToolNode(tools, handle_tool_errors=lambda e: str(e))

# Function to decide whether to continue tool usage or end the process
def should_continue(state: GraphsState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:  # Check if the last message has any tool calls
        return "tools"  # Continue to tool execution
    return "__end__"  # End the conversation if no tool is needed


# Core invocation of the model
def _call_model(state: GraphsState):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    llm = ChatOpenAI(
        temperature=0.7,
        streaming=True,
        # specifically for OpenAI we have to set parallel tool call to false
        # because of st primitively visually rendering the tool results
    ).bind_tools(tools, parallel_tool_calls=False)
    response = llm.invoke(messages)
    return {"messages": [response]}  # add the response to the messages using LangGraph reducer paradigm


# Define the structure (nodes and directional edges between nodes) of the graph
graph.add_edge(START, "modelNode")
graph.add_node("tools", tool_node)
graph.add_node("modelNode", _call_model)

# Add conditional logic to determine the next step based on the state (to continue or to end)
graph.add_conditional_edges(
    "modelNode",
    should_continue,  # This function will decide the flow of execution
)
graph.add_edge("tools", "modelNode")

# Compile the state graph into a runnable object
graph_runnable = graph.compile()


def invoke_our_graph(st_messages, callables):
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    return graph_runnable.invoke({"messages": st_messages}, config={"callbacks": callables})


def get_tools_list():
    print(f"TOOLS {tools}")
    return tools
