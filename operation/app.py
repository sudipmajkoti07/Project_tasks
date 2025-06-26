import os
from dotenv import load_dotenv
from typing import TypedDict, List
from typing_extensions import Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain.tools import tool

from langchain_qdrant import Qdrant as QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings as SentenceTransformerEmbeddings

from qdrant_client import QdrantClient
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL")
max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "1000"))

memory = MemorySaver()

llm = ChatGroq(
    groq_api_key=api_key,
    model=model_name,
    max_tokens=max_tokens,
)

embedding_model_name = "all-MiniLM-L6-v2"
embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model_name)


qdrant_client = QdrantClient(host="localhost", port=6333)
collection_name = "documents"

vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=collection_name,
    embeddings=embedding_model,
)

retriever = vectorstore.as_retriever()


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


@tool
def transformer_retriever_tool(state: State) -> dict:
    """Retrieve relevant documents from Qdrant and answer using context."""
    query = state["messages"][-1].content
    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = llm.invoke(
        f"Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {query}"
    )
    return {"messages": [{"role": "assistant", "content": answer.content}]}


graph_builder = StateGraph(State)
tools = [transformer_retriever_tool]
llm_with_tools = llm.bind_tools(tools)

system_prompt = """
You are a helpful assistant.

If the user asks a specific question that requires information from the documents, call the retrieval tool.

If the question is general, casual, or not related to the documents, answer directly without calling any tool.
and make the response very short and concise.
"""


def chatbot(state: State) -> dict:
    messages = [HumanMessage(content=system_prompt)] + state["messages"]
    llm_response = llm_with_tools.invoke(messages)
    return {"messages": state["messages"] + [llm_response]}


def custom_decision_function(state: State):
    last_message = state["messages"][-1]
    if (
        isinstance(last_message, AIMessage)
        and hasattr(last_message, "tool_calls")
        and last_message.tool_calls
    ):
        return "tools"
    else:
        return "end"


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    custom_decision_function,
    {
        "tools": "tools",
        "end": END,
    },
)

graph = graph_builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "1"}}

def process_query(user_query: str) -> dict:
    initial_state = {"messages": [HumanMessage(content=user_query)]}
    final_state = graph.invoke(initial_state, config=config)
    final_messages = final_state["messages"]
    response = final_messages[-1].content if final_messages else "No response generated."
    return {"response": response}