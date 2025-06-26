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
from langgraph.checkpoint.memory import MemorySaver
from datetime import date

from database.db import insert_booking
import smtplib
from email.message import EmailMessage


today = date.today()
formatted_date = today.strftime("%Y-%m-%d")



# Load environment variables
load_dotenv()

# LLM Configuration
groq_api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL")
max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "1000"))

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Memory Checkpointing
memory = MemorySaver()

# LLM Initialization
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model=model_name,
    max_tokens=max_tokens,
)

# State Definition
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


@tool
def update_table(
    full_name: str,  # Full name of the candidate booking the interview
    email: str,      # Email address of the candidate
    date: str,       # Interview date in 'YYYY-MM-DD' format
    time: str        # Interview time in 'HH:MM' 24-hour format
) -> dict:
    """
    Receives booking details as parameters and inserts them into the database.

    Args:
        full_name (str): Full name of the candidate booking the interview.
        email (str): Email address of the candidate.
        date (str): Interview date in 'YYYY-MM-DD' format.
        time (str): Interview time in 'HH:MM' 24-hour format.

    Returns:
        dict: Confirmation message.
    """
    # Insert booking into the database
    insert_booking(full_name, email, date, time)

    return {"content": f"Booking confirmed for {full_name} on {date} at {time}."}

@tool
def send_confirmation_email(
    full_name: str,  # Full name of the candidate
    email: str,      # Candidate's email (can be used in email body)
    date: str,       # Interview date
    time: str        # Interview time
) -> dict:
    """
    Sends a confirmation email to the fixed CONFIRM_TO_EMAIL address
    with the interview booking details.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Interview Booking Confirmation for {full_name}"
    msg["From"] = SMTP_USER
    msg["To"] = email
    body = (
        f"Interview Booking Details:\n\n"
        f"Full Name: {full_name}\n"
        f"Email: {email}\n"
        f"Date: {date}\n"
        f"Time: {time}\n"
    )
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return {"content": "Confirmation email sent successfully."}
    except Exception as e:
        return {"content": f"Failed to send email: {e}"}

# System Prompt
system_prompt = f"""
You are an interview booking assistant. Collect the user's full name, email, date (YYYY-MM-DD), and time (in HH:MM AM/PM format) for the interview.
When all details are provided, confirm the details before updating in the database.
After confirmation, insert the booking into the database.
Then send a confirmation email to the user.
{formatted_date} is today's date.
don't allow user to make appointment in the past
Make the response short.
"""

# Tools and LLM with Tools
tools = [update_table, send_confirmation_email]
llm_with_tools = llm.bind_tools(tools)

# Chatbot Node
def chatbot(state: State) -> dict:
    messages = [HumanMessage(content=system_prompt)] + state["messages"]
    llm_response = llm_with_tools.invoke(messages)
    return {"messages": state["messages"] + [llm_response]}

# Custom Decision Logic
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

# Graph Construction
graph_builder = StateGraph(State)
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

# Compile the Graph
graph = graph_builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "2"}}

# Callable from main

def process_booking(user_query: str) -> dict:
    initial_state = {"messages": [HumanMessage(content=user_query)]}
    final_state = graph.invoke(initial_state, config=config)
    final_messages = final_state["messages"]
    response = final_messages[-1].content if final_messages else "No response generated."
    return {"response": response}