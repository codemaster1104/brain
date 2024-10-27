from typing import Dict, List, Any, Optional
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import requests
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

# Initialize LLMs
llama_llm = CustomLLM()
llama_tool = CustomLLM2()

# Classifier prompt to determine conversation type
CLASSIFIER_PROMPT = """Analyze if the following input requires a simple conversational response or detailed analytical thinking.

Input: {input}

Consider:
1. Is this casual greeting/conversation?
2. Does this require analytical thinking?
3. Is this a complex query needing detailed explanation?

Response Type: {{"type": "casual"}} or {{"type": "analytical"}}

Classification:"""

# Casual conversation prompt
CASUAL_PROMPT = """Respond naturally to this casual conversation:

User: {input}

Response:"""

# Main chain of thought template (using previous COT_PROMPT_TEMPLATE)
COT_PROMPT_TEMPLATE = """System: {system}

Input: {input}

Let's solve this systematically:

1. Problem Understanding:
{understanding_prompt}

2. Initial Analysis:
{analysis_prompt}

3. Tool Consideration:
{tool_prompt}

4. Solution Development:
{solution_prompt}

5. Verification:
{verification_prompt}

Final Answer: {output_format}
"""

class LLMSmartChainOfThought:
    def __init__(self, 
                 primary_llm: LLM = llama_llm,
                 tool_llm: LLM = llama_tool,
                 temperature: float = 0.1,
                 verbose: bool = True):
        self.primary_llm = primary_llm
        self.tool_llm = tool_llm
        self.temperature = temperature
        self.verbose = verbose
        
        # Initialize classifier prompt
        self.classifier_prompt = PromptTemplate(
            input_variables=["input"],
            template=CLASSIFIER_PROMPT
        )
        
        # Initialize conversation prompts
        self.casual_prompt = PromptTemplate(
            input_variables=["input"],
            template=CASUAL_PROMPT
        )
        
        self.cot_prompt = PromptTemplate(
            input_variables=["system", "input", "understanding_prompt", 
                           "analysis_prompt", "tool_prompt", "solution_prompt",
                           "verification_prompt", "output_format"],
            template=COT_PROMPT_TEMPLATE
        )
        
        # Initialize chains
        self.classifier_chain = LLMChain(
            llm=self.primary_llm,
            prompt=self.classifier_prompt,
            verbose=self.verbose
        )
        
        self.casual_chain = LLMChain(
            llm=self.primary_llm,
            prompt=self.casual_prompt,
            verbose=self.verbose
        )
        
        self.cot_chain = LLMChain(
            llm=self.primary_llm,
            prompt=self.cot_prompt,
            verbose=self.verbose
        )

    def classify_input(self, input_text: str) -> str:
        """
        Use LLM to classify input as casual or analytical
        """
        try:
            classification = self.classifier_chain.run(input=input_text)
            return "casual" if "type\": \"casual" in classification.lower() else "analytical"
        except Exception as e:
            print(f"Classification error: {e}")
            # Default to analytical if classification fails
            return "analytical"

    def process(self, 
                input_text: str,
                output_format: str = "Provide a clear response.",
                use_tool: bool = False) -> Dict[str, Any]:
        """
        Process input using LLM classification and appropriate response generation
        """
        try:
            # First, classify the input using LLM
            input_type = self.classify_input(input_text)
            
            # Handle casual conversation
            if input_type == "casual":
                response = self.casual_chain.run(input=input_text)
                
                return {
                    "status": "success",
                    "response_type": "casual",
                    "response": response.strip(),
                    "metadata": {
                        "model_used": "primary_llm",
                        "classification": "casual"
                    }
                }
            
            # Handle analytical queries
            else:
                current_llm = self.tool_llm if use_tool else self.primary_llm
                
                prompt_args = {
                    "system": "You are an analytical reasoning engine that breaks down complex problems systematically.",
                    "input": input_text,
                    "understanding_prompt": "- Key aspects:\n- Core challenges:\n- Context required:",
                    "analysis_prompt": "- Initial insights:\n- Key considerations:\n- Potential approaches:",
                    "tool_prompt": "- Required resources:\n- Analytical methods:\n- Data needs:",
                    "solution_prompt": "- Step-by-step analysis:\n- Key findings:\n- Recommendations:",
                    "verification_prompt": "- Validation points:\n- Potential issues:\n- Confidence level:",
                    "output_format": output_format
                }
                
                response = self.cot_chain.run(**prompt_args)
                
                return {
                    "status": "success",
                    "response_type": "analytical",
                    "full_response": response,
                    "metadata": {
                        "model_used": "tool_llm" if use_tool else "primary_llm",
                        "classification": "analytical",
                        "temperature": self.temperature
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "metadata": {
                    "model_used": "primary_llm",
                    "attempted_classification": input_type if 'input_type' in locals() else "unknown"
                }
            }

def example_usage():
    """
    Example usage of the LLM-based classifier and processor
    """
    processor = LLMSmartChainOfThought()
    
    # Test cases
    test_inputs = [
        "Hi there!",
        "How are you today?",
        "Analyze the impact of quantum computing on current encryption methods",
        "What's the best approach to implement a distributed caching system?",
        "Thanks for your help!",
        "Could you explain the benefits and drawbacks of microservices?"
    ]
    
    results = []
    for input_text in test_inputs:
        print(f"\nProcessing: {input_text}")
        result = processor.process(input_text)
        print(f"Classification: {result['response_type']}")
        if result['response_type'] == 'casual':
            print(f"Response: {result['response']}")
        else:
            print(f"Analytical Response Available: {len(result['full_response'])} characters")
        results.append(result)
    
    return results

def interactive_mode():
    """
    Interactive testing mode
    """
    processor = LLMSmartChainOfThought()
    
    print("Enter messages (type 'exit' to quit):")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'exit':
            break
            
        result = processor.process(user_input)
        print("\nResponse Type:", result['response_type'])
        if result['response_type'] == 'casual':
            print("Response:", result['response'])
        else:
            print("Analytical Response:", result['full_response'])

if __name__ == "__main__":
    interactive_mode()