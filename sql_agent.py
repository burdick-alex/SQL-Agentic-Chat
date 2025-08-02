import os
import sqlite3
import sqlparse
import requests
from datetime import datetime
from typing import Annotated, Sequence, TypedDict

from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages  # helper function to add messages to the state

# Read your API key from the environment variable or set it manually
api_key = os.getenv("GEMINI_API_KEY")

geolocator = Nominatim(user_agent="weather-app")

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    number_of_steps: int


class HumanInputSchema(BaseModel):
    prompt: str = Field(description="The prompt to display to the user asking for input")

@tool("get_human_input", args_schema=HumanInputSchema, return_direct=True)
def get_human_input(prompt: str):
    """Gets input from the human user using Python's input() function. Displays the given prompt and returns the user's response."""
    try:
        user_input = input(f"{prompt}: ")
        return {"user_input": user_input}
    except Exception as e:
        return {"error": f"Failed to get user input: {str(e)}"}

class SQLQueryInput(BaseModel):
    query: str = Field(description="The SQL query to execute on the titanic dataset database")

@tool("execute_titanic_sql_query", args_schema=SQLQueryInput, return_direct=True)
def execute_titanic_sql_query(query: str):
    """Executes the given SQL query on the titanic dataset database and returns the result."""
    #run the query on the titanic sqlite3 database
    query_type = sqlparse.parse(query)[0].get_type().lower()
    if query_type == "select":
        conn = sqlite3.connect('data/titanic.db')
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
    else:
        return {"error": "Only read-only queries are supported"}
    return {"result": result}

class FinanceSQLQueryInput(BaseModel):
    query: str = Field(description="The SQL query to execute on the finance transaction dataset database")

@tool("execute_finance_sql_query", args_schema=FinanceSQLQueryInput, return_direct=True)
def execute_finance_sql_query(query: str):
    """Executes the given SQL query on the finance transaction dataset database and returns the result."""
    #run the query on the finance transaction sqlite3 database
    query_type = sqlparse.parse(query)[0].get_type().lower()
    if query_type == "select":
        conn = sqlite3.connect('data/aug_personal_transactions_with_UserId.db')
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
    else:
        return {"error": "Only read-only queries are supported"}
    return {"result": result}

#create a tool to get the table names in the finance transaction dataset database
@tool("get_table_names", return_direct=True)
def get_table_names():
    """Gets the table names in the finance transaction dataset database."""
    conn = sqlite3.connect('data/aug_personal_transactions_with_UserId.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    result = cursor.fetchall()
    conn.close()
    return {"result": result}

class TableNameInput(BaseModel):
    table_name: str = Field(description="The SQL query to execute on the finance transaction dataset database")

@tool("get_table_columns", args_schema=TableNameInput, return_direct=True)
def get_table_columns(table_name: str):
    """Gets the columns of the given table in the finance transaction dataset database."""
    #run the query on the finance transaction sqlite3 database
    try:
        conn = sqlite3.connect('data/aug_personal_transactions_with_UserId.db')
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        result = cursor.fetchall()
        conn.close()
        return {"result": result}
    except Exception as e:
        return {"error": f"Failed to get table columns: {str(e)}"}

@tool("get_table_row_example", args_schema=TableNameInput, return_direct=True)
def get_table_row_example(table_name: str):
    """Gets an example of a row in the given table in the finance transaction dataset database."""
    #run the query on the finance transaction sqlite3 database
    try:
        conn = sqlite3.connect('data/aug_personal_transactions_with_UserId.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        result = cursor.fetchall()
        conn.close()
        return {"result": result}
    except Exception as e:
        return {"error": f"Failed to get table row example: {str(e)}"}

tools = [get_human_input, execute_titanic_sql_query, execute_finance_sql_query, get_table_names, get_table_columns, get_table_row_example]

# Create LLM class
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-flash",
    temperature=1.0,
    max_retries=2,
    google_api_key=api_key,
)

# Bind tools to the model
model = llm.bind_tools(tools)

tools_by_name = {tool.name: tool for tool in tools}

# Define our tool node
def call_tool(state: AgentState):
    outputs = []
    # Iterate over the tool calls in the last message
    for tool_call in state["messages"][-1].tool_calls:
        #Log the tool call
        print(f"Tool call: {tool_call}")
        # Get the tool by name
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        #Log the tool result
        print(f"Tool result: {tool_result}")
        outputs.append(
            ToolMessage(
                content=tool_result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

def call_model(
    state: AgentState,
    config: RunnableConfig,
):
    # Create system message
    system_message = SystemMessage(content="""You are a helpful AI assistant with access to various tools including:
        - SQL query execution on Titanic dataset
        - SQL query execution on finance transaction dataset
        - Database exploration tools (table names, columns, sample data)

        When users ask questions, use the appropriate tools to provide accurate and helpful responses. 
        For SQL queries, always use the correct database (Titanic or aug_personal_transactions_with_userid) based on the context.
        Be concise but thorough in your explanations."""
    )

    # Combine system message with existing messages
    all_messages = [system_message] + state["messages"]
    
    # Invoke the model with the system prompt and the messages
    response = model.invoke(all_messages, config)
    # We return a list, because this will get added to the existing messages state using the add_messages reducer
    return {"messages": [response]}

# Define the conditional edge that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    # If the last message is not a tool call, then we finish
    if not messages[-1].tool_calls:
        return "end"
    # default to continue
    return "continue"


