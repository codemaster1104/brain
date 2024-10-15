import requests
from langchain.llms.base import LLM
from typing import Optional, List, Dict, Any
from langchain.schema import PromptValue
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
import requests
from typing import Dict, List
from langchain.tools import BaseTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import GithubFileLoader
from langchain_community.document_loaders import GitHubIssuesLoader
import subprocess
from langchain.tools import BaseTool
import os
import json
from langchain.memory import ConversationBufferWindowMemory
from langchain.base_language import BaseLanguageModel
from langchain.agents import AgentExecutor
from langchain_community.tools.file_management.copy import CopyFileTool
from langchain_community.tools.file_management.delete import DeleteFileTool
from langchain_community.tools.file_management.file_search import FileSearchTool
from langchain_community.tools.file_management.list_dir import ListDirectoryTool
from langchain_community.tools.file_management.move import MoveFileTool
from langchain_community.tools.file_management.read import ReadFileTool
from langchain_community.tools.file_management.write import WriteFileTool
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.tools.gmail.create_draft import GmailCreateDraft
from langchain_community.tools.gmail.get_message import GmailGetMessage
from langchain_community.tools.gmail.get_thread import GmailGetThread
from langchain_community.tools.gmail.search import GmailSearch
from langchain_community.tools.gmail.send_message import GmailSendMessage
from langchain_community.tools.gmail.utils import get_gmail_credentials
from langchain_community.tools.google_jobs.tool import GoogleJobsQueryRun
from langchain_community.tools.human.tool import HumanInputRun
from langchain_community.tools.google_jobs.tool import GoogleJobsQueryRun
import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, Graph
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain.schema import HumanMessage

###########################LLM###########################

class CustomLLM(LLM):                                                                            ## LLAMA 3.0
    api_base_url: str = "https://llama.us.gaianet.network/v1"
    model_name: str = "llama"
    api_key: str = "GAIA"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000  
        }
        if stop:
            payload["stop"] = stop

        response = requests.post(f"{self.api_base_url}/completions", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["text"].strip()  
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    @property
    def _llm_type(self) -> str:
        return "custom_llama"  
    

class CustomLLM2(LLM):                                                                          ##LLAMA Groq Tool
    api_base_url: str = "https://llamatool.us.gaianet.network/v1"
    model_name: str = "llama"
    api_key: str = "GAIA"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000  
        }
        if stop:
            payload["stop"] = stop

        response = requests.post(f"{self.api_base_url}/completions", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["text"].strip() 
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    @property
    def _llm_type(self) -> str:
        return "custom_llama"


llama_llm = CustomLLM()
llama_tool = CustomLLM2()



###########################Agents###########################

memory = ConversationBufferMemory(memory_key="chat_history")
# memory=ConversationBufferWindowMemory(k=5)
tools= [DuckDuckGoSearchRun(),
        HumanInputRun()]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    tools: list[BaseTool]

# Define the agent node
def agent(state: AgentState) -> dict:
    messages = state["messages"]
    tools = state["tools"]
    
    # Use the existing agent setup
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent_chain = initialize_agent(
        tools,
        llama_tool,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True
    )
    
    result = agent_chain.invoke({"input": messages[-1].content, "chat_history": messages[:-1]})
    return {
        "messages": [result["output"]],
        "next": "call_tool" if "tool" in result else END
    }

# Define the tool executor node
def call_tool(state: AgentState):
    messages = state["messages"]
    tools = state["tools"]
    last_message = messages[-1]
    
    tool_executor = ToolExecutor(tools)
    response = tool_executor.invoke(last_message)
    return {"messages": [response], "next": "agent"}

# Create the workflow
workflow = Graph()

# Add agent and tool nodes
workflow.add_node("agent", agent)
workflow.add_node("call_tool", call_tool)

# Add edges
workflow.add_edge("agent", "call_tool")
workflow.add_edge("call_tool", "agent")

# Set the entry point
workflow.set_entry_point("agent")

# Compile the graph
app = workflow.compile()

# Function to process queries
def process_query(query: str):
    tools = tools
    
    result = app.invoke({
        "messages": [HumanMessage(content=query)],
        "tools": tools
    })
    
    print(result['messages'][-1].content)

# Main function
def main():
    try:
        query = input("Enter your query (e.g., 'create a simple calculator'): ")
        process_query(query)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please ensure all required packages are installed and up-to-date.")

if __name__ == "__main__":
    main()

