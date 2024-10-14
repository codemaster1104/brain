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
from bs4 import BeautifulSoup
import PyPDF2

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
    
class PDFResumeParserTool(BaseTool):
    name = "pdf_resume_parser"
    description = "A tool for parsing PDF resumes and extracting information"

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _run(self, pdf_path: str) -> str:
        resume_text = self._extract_text_from_pdf(pdf_path)
        prompt = f"""
        Parse the following resume and extract key information in JSON format:
        Resume:
        {resume_text}

        Please extract and format the information as follows:
        {{
            "name": "Full Name",
            "email": "email@example.com",
            "phone": "phone number",
            "skills": ["skill1", "skill2", ...],
            "education": [
                {{"degree": "Degree Name", "institution": "Institution Name", "year": "Graduation Year"}},
                ...
            ],
            "experience": [
                {{"title": "Job Title", "company": "Company Name", "duration": "Start Date - End Date", "description": "Brief description of responsibilities"}},
                ...
            ]
        }}
        """
        parsed_resume = llama_llm(prompt)
        try:
            return json.loads(parsed_resume)
        except json.JSONDecodeError:
            return {"error": "Failed to parse resume. Please check the PDF file and try again."}

    async def _arun(self, pdf_path: str) -> str:
        return self._run(pdf_path)
    
class InternshipSearchTool(BaseTool):
    name = "internship_search"
    description = "A tool for searching internship opportunities based on resume information."

    def _run(self, query: str) -> str:
        # Using LinkedIn Jobs search as an example
        url = "https://www.linkedin.com/jobs/search"
        params = {
            "keywords": query,
            "location": "United States",  # You can make this dynamic based on user preference
            "f_JT": "I",  # Filter for internships
            "sortBy": "R"  # Sort by relevance
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        jobs = []
        for job in soup.find_all('div', class_='base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card'):
            title = job.find('h3', class_='base-search-card__title').text.strip()
            company = job.find('h4', class_='base-search-card__subtitle').text.strip()
            location = job.find('span', class_='job-search-card__location').text.strip()
            link = job.find('a', class_='base-card__full-link')['href']
            
            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "apply_link": link,
                "requires_cold_email": False
            })
        
        return json.dumps(jobs[:5])  # Return top 5 results

    async def _arun(self, query: str) -> str:
        return self._run(query)
    
class CoverLetterGeneratorTool(BaseTool):
    name = "cover_letter_generator"
    description = "A tool for generating cover letters based on combined resume and job information."

    def _run(self, combined_input: str) -> str:
        # Split the input into resume_info and job_info
        resume_info, job_info = combined_input.split("###JOB_INFO###")

        prompt = f"""
        Generate a tailored cover letter based on the following resume and job information:

        Resume:
        {resume_info}

        Job Information:
        {job_info}

        Please write a professional cover letter that highlights the relevant skills and experiences from the resume that match the job requirements. The cover letter should be engaging, concise, and demonstrate enthusiasm for the position.
        """

        ans=llama_llm(prompt)
        print(ans)
        return ans

    async def _arun(self, combined_input: str) -> str:
        return self._run(combined_input)


# class ApplicationHandlerTool(BaseTool):
#     name = "application_handler"
#     description = "A tool for handling job applications or creating cold emails."

#     def _run(self, job_info: str, cover_letter: str) -> str:
#         job = json.loads(job_info)
#         if job['requires_cold_email']:
#             # In a real implementation, you would send an actual email here
#             return f"Cold email prepared for {job['company']} with the generated cover letter. Please review and send manually."
#         else:
#             # In a real implementation, you might use Selenium to automate application submission
#             return f"Application ready for submission via {job['apply_link']}. Please review the cover letter and submit manually."

#     async def _arun(self, job_info: str, cover_letter: str) -> str:
#         return self._run(job_info, cover_letter)


#############################################agents####################################################


memory = ConversationBufferMemory(memory_key="chat_history")
# memory=ConversationBufferWindowMemory(k=5)
tools= [PDFResumeParserTool(),
    InternshipSearchTool(),
    CoverLetterGeneratorTool()
    ]

agent = initialize_agent(
    tools,
    llama_tool,
    # agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def process_query(query: str):
    response = agent.invoke( {"input": f"Parse the resume from this PDF file: {query}. Then, find relevant internship opportunities. For each opportunity, generate a cover letter and prepare the application or cold email."
        })
    print(response)

def main():
    try:
        # query = input("Enter your query (e.g., 'create a simple calculator'): ")
        path="22135150_Akshat_Shrivastava_A3 (1)-1.pdf"
        process_query(path)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please ensure all required packages are installed and up-to-date.")

if __name__ == "__main__":
    main()