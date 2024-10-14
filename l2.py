import sys

try:
    import openai
except ImportError:
    print("Error: Failed to import openai. Please install it using 'pip install openai'.")
    sys.exit(1)

import os
import time
import json
import re

API_BASE_URL = "https://llama.us.gaianet.network/v1"
MODEL_NAME = "llama"
API_KEY = "GAIA"

def understanding_prompt(source_text):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Parse the prompt and provide an overall understanding of the text, then divide the task at hand into subtasks"},
            {"role": "user", "content": source_text},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def logical(source_text):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "process the given data logically and provide logical solutions for all subtasks"},
            {"role": "user", "content": source_text},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def fout(source_text):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Provide the final output of the task in differnt sections with each section starting with '#$%^&<section_heading>#$%^&' and code it out"},
            {"role": "user", "content": source_text},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def extract_json(text):
    # Use a regex pattern to find JSON-like structures
    json_pattern = r'\{(?:[^{}]|(?R))*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if not matches:
        print("Error: No JSON-like structure found in the text")
        return None
    
    # Try to parse each match, starting with the longest one
    for match in sorted(matches, key=len, reverse=True):
        try:
            # Replace newlines within string values
            json_str = re.sub(r'("(?:(?=\\)\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})|[^"\\\n\r])*")',
                              lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r'),
                              match)
            
            # Remove whitespace outside of strings
            json_str = re.sub(r'\s+(?=(?:[^"]*"[^"]*")*[^"]*$)', '', json_str)
            
            # Parse the JSON
            data = json.loads(json_str)
            
            # Validate that we have the expected keys
            if all(key in data for key in ['html', 'css', 'js']):
                return data
            else:
                print("Warning: Parsed JSON doesn't contain all expected keys (html, css, js)")
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON structure. Error: {str(e)}")
            print("Problematic JSON string:")
            print(json_str)
    
    print("Error: Could not extract valid JSON data with required keys from the model output")
    return None

def create_and_save_files(output, project_name):
    print("Raw output from LLM:")
    print(output)
    
    data = extract_json(output)
    if not data:
        print("Error: Could not extract valid JSON data from the model output")
        return False

    project_folder = os.path.join("projects", project_name)
    os.makedirs(project_folder, exist_ok=True)

    for file_type, content in data.items():
        file_path = os.path.join(project_folder, f"index.{file_type}")
        with open(file_path, 'w') as f:
            f.write(content)

    print(f"Files created in {project_folder}")
    return True

def test_project(project_name):
    project_folder = os.path.join("projects", project_name)
    index_html = os.path.join(project_folder, "index.html")
    
    if os.path.exists(index_html):
        print(f"Project {project_name} created successfully.")
        print(f"You can open {index_html} in a web browser to test it.")
        return True
    else:
        print(f"Error: index.html not found in {project_folder}")
        return False

def improve_project(project_name, feedback):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    project_folder = os.path.join("projects", project_name)
    
    with open(os.path.join(project_folder, "index.html"), 'r') as f:
        html_content = f.read()
    with open(os.path.join(project_folder, "index.css"), 'r') as f:
        css_content = f.read()
    with open(os.path.join(project_folder, "index.js"), 'r') as f:
        js_content = f.read()

    prompt = f"""
    Based on the following feedback, improve the project:
    
    Feedback: {feedback}
    
    Current HTML:
    {html_content}
    
    Current CSS:
    {css_content}
    
    Current JS:
    {js_content}
    
    Provide improved versions of these files as a JSON object with keys 'html', 'css', and 'js'.
    You may include additional explanations or context if necessary.
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a web development expert. Improve the given project based on the feedback."},
            {"role": "user", "content": prompt},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    
    improved_output = chat_completion.choices[0].message.content
    return create_and_save_files(improved_output, project_name)


def process_query(query):
    ug = understanding_prompt(query)
    print("Understanding:", ug)

    logic = logical(ug)
    print("Logic:", logic)

    final_output = fout(logic)
    print("Final output generated")

    project_name = query.replace(" ", "_").lower()
    if create_and_save_files(final_output, project_name):
        if test_project(project_name):
            user_feedback = input("Do you want to improve the project? (yes/no): ")
            if user_feedback.lower() == 'yes':
                feedback = input("Please provide your feedback: ")
                if improve_project(project_name, feedback):
                    print(f"Project {project_name} has been improved based on your feedback.")
                else:
                    print("Failed to improve the project.")
        else:
            print("Project creation failed.")
    else:
        print("Failed to create project files.")

def main():
    try:
        query = input("Enter your query (e.g., 'make a calculator'): ")
        process_query(query)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please ensure all required packages are installed and up-to-date.")

if __name__ == "__main__":
    main()