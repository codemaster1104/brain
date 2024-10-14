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

####################################################LLM####################################################

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

####################################################tools####################################################

class InternetSearchTool(BaseTool):
    name = "internet_search"
    description = "A tool for searching the internet using DuckDuckGo. Use this when you need to find current information about a topic."

    def _search(self, query: str) -> List[Dict[str, str]]:
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1',
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        results = []
        if 'AbstractText' in data and data['AbstractText']:
            results.append({
                'title': data['Heading'],
                'snippet': data['AbstractText'],
                'link': data['AbstractURL']
            })
        
        for result in data.get('RelatedTopics', [])[:5]:  # Limit to top 5 related results
            if 'Text' in result:
                results.append({
                    'title': result.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                    'snippet': result['Text'],
                    'link': result.get('FirstURL', '')
                })
        
        return results

    def _run(self, query: str) -> str:
        results = self._search(query)
        if not results:
            return "No results found."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"{i}. {result['title']}\n   {result['snippet']}\n   URL: {result['link']}\n")
        
        return "\n".join(formatted_results)

    async def _arun(self, query: str) -> str:
        # For simplicity, we're calling the synchronous version here.
        # In a production environment, you'd want to implement a truly asynchronous version.
        return self._run(query)
    


class CodeGenerationAndExecutionTool(BaseTool):
    name = "code_generation_and_execution"
    description = "A tool that generates Python code based on a given task and executes it in a secure environment."

    def _run(self, task: str) -> str:
        # Step 1: Generate code (this would typically be done by an LLM)
        generated_code = self._generate_code(task)

        # Step 2: Execute the generated code
        result = self._execute_code(generated_code)

        return f"Generated Code:\n{generated_code}\n\nExecution Result:\n{result}"

    def _generate_code(self, task: str) -> str:
        # Use llama_llm (your custom LLM) to generate the code based on the provided task
        prompt = f"""
        You are a helpful assistant. Write a Python function that solves the following task:
        Task: {task}
        Make sure to include a main function that runs the solution and prints the result.
        """
        
        try:
            # Generate code using the LLM
            generated_code = llama_llm(prompt)
            
            # Optionally, you can format or validate the generated code here if needed
            return generated_code
        
        except Exception as e:
            # In case of an error, fall back to a hardcoded function
            return f"""
                        def solve_task():
                            print("Error while solving task: {task}")
                            # Placeholder implementation due to error
                            return "Task could not be completed"

                        result = solve_task()
                        print(result)
                        """


    def _execute_code(self, code: str) -> str:
        # Create a temporary Python file
        with open("temp_code.py", "w") as f:
            f.write(code)

        # Execute the code in a separate process with restrictions
        try:
            result = subprocess.run(
                ["python", "-u", "temp_code.py"],
                capture_output=True,
                text=True,
                timeout=5,  # Set a timeout to prevent infinite loops
            )
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out"
        finally:
            # Clean up the temporary file
            subprocess.run(["rm", "temp_code.py"])

    async def _arun(self, query: str) -> str:
        # For simplicity, we're calling the synchronous version here
        return self._run(query)
    


# class ContextAwareFileFolderGenerationTool(BaseTool):
#     name = "context_aware_file_folder_generation"
#     description = "A tool that generates a file and folder structure based on a given specification, when need to create files or a project structure."

#     def _run(self, query: str) -> str:
#         if not self._should_generate_files(query):
#             return "No file or folder generation is needed for this query."

#         try:
#             # Extract the structure from the query
#             structure = self._extract_structure(query)
            
#             # Generate the file and folder structure
#             root_dir = "generated_structure"
#             self._generate_structure(root_dir, structure)
            
#             return f"File and folder structure generated successfully in '{root_dir}' directory."
#         except json.JSONDecodeError:
#             return "Error: Invalid structure specification provided."
#         except Exception as e:
#             return f"Error: {str(e)}"

#     def _should_generate_files(self, query: str) -> bool:
#         # Check if the query explicitly mentions file/folder creation or project structure
#         keywords = ['create files', 'generate files', 'make folders', 'project structure', 'file structure']
#         return any(keyword in query.lower() for keyword in keywords)

#     def _extract_structure(self, query: str) -> Dict[str, Any]:
#         # This is a simplified extraction. In a real scenario, you might use an LLM to parse the query
#         # and generate a proper structure.
#         structure = {
#             "project": {
#                 "src": {
#                     "main.py": "# Main file content"
#                 },
#                 "tests": {
#                     "test_main.py": "# Test file content"
#                 },
#                 "README.md": "# Project README"
#             }
#         }
#         return structure

#     def _generate_structure(self, current_path: str, structure: Dict[str, Any]):
#         os.makedirs(current_path, exist_ok=True)
        
#         for name, content in structure.items():
#             path = os.path.join(current_path, name)
            
#             if isinstance(content, dict):
#                 # If content is a dictionary, it's a folder
#                 self._generate_structure(path, content)
#             else:
#                 # If content is not a dictionary, it's a file
#                 with open(path, 'w') as f:
#                     f.write(str(content))

#     async def _arun(self, query: str) -> str:
#         # For simplicity, we're calling the synchronous version here
#         return self._run(query)


class LLMFileFolderGenerationTool(BaseTool):
    name = "llm_file_folder_generation"
    description = "A tool that generates a file and folder structure based on a given specification, when need to create files or a project structure."
    # llm: BaseLanguageModel

    def _run(self, query: str) -> str:
        if not self._should_generate_files(query):
            return "No file or folder generation is needed for this query."

        try:
            structure = self._extract_structure(query)
            root_dir = os.getcwd()
            # os.mkdir(agent_result)
            self._generate_structure(root_dir, structure)
            return f"File and folder structure generated successfully in '{root_dir}' directory."
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def _should_generate_files(self, query: str) -> bool:
        prompt = f"""
        Determine if the following query is requesting to create files or a project structure:
        Query: {query}
        Answer with 'Yes' or 'No'.
        """
        response = llama_tool(prompt)
        return response.strip().lower() == 'yes'

    def _extract_structure(self, query: str) -> Dict[str, Any]:
        prompt = f"""
        Based on the following query, generate a JSON structure representing the requested file and folder structure.
        Use the following format:
        {{
            "project_name": {{
                "folder1": {{
                    "file1.ext": "file content",
                    "subfolder": {{
                        "file2.ext": "file content"
                    }}
                }},
                "folder2": {{
                    "file3.ext": "file content"
                }},
                "Readme.txt": "Project README content"
            }}
        }}
        Query: {query}
        JSON structure:
        """

        response = self.llm(prompt)

        print(response)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Failed to generate a valid file structure. Please try again with a more specific request.")

    def _generate_structure(self, root_dir: str, structure: Dict[str, Any]) -> None:
        for name, content in structure.items():
            path = os.path.join(root_dir, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                self._generate_structure(path, content)
            else:
                with open(path, 'w') as f:
                    f.write(str(content))

    async def _arun(self, query: str) -> str:
        return self._run(query)

#############################################agents####################################################


memory = ConversationBufferMemory(memory_key="chat_history")
# memory=ConversationBufferWindowMemory(k=5)
tools= [InternetSearchTool(),CodeGenerationAndExecutionTool(),LLMFileFolderGenerationTool(llm=llama_tool)]

agent = initialize_agent(
    tools,
    llama_tool,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    # agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def process_query(query: str):
    response = agent.invoke(query)
    print(response)

def main():
    try:
        query = input("Enter your query (e.g., 'create a simple calculator'): ")
        process_query(query)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please ensure all required packages are installed and up-to-date.")

if __name__ == "__main__":
    main()