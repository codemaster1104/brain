import sys
import os
import time
import json
import re

try:
    import openai
except ImportError:
    print("Error: Failed to import openai. Please install it using 'pip install openai'.")
    sys.exit(1)

API_BASE_URL = "https://llamatool.us.gaianet.network/v1"
MODEL_NAME = "llama"
API_KEY = "GAIA"

API2="https://yicoder.us.gaianet.network/v1"
MODEL_NAME2="yicoder"
API_KEY2="GAIA"

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
            {"role": "system", "content": "Process the given data logically and provide logical solutions for all subtasks"},
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
            {"role": "system", "content": "Provide the final output of the task as a Python script only. Include necessary imports and comments.All the explanation should be comneted out nothing other than code should be uncommented dont even inclue ''' python''' or '''python''' in the code"},
            {"role": "user", "content": source_text},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def create_documentation(project_name, python_content):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    prompt = f"""
    Create a README.md file for the following Python project:

    Project Name: {project_name}

    Python Code:
    {python_content}

    Include the following sections:
    1. Project Description
    2. Dependencies
    3. Installation
    4. Usage
    5. Example
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a technical writer. Create a comprehensive README.md file for the given Python project."},
            {"role": "user", "content": prompt},
        ],
        model=MODEL_NAME,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def create_and_save_files(output, project_name):
    print("Raw output from LLM:")
    print(output)
    
    project_folder = os.path.join("projects", project_name)
    os.makedirs(project_folder, exist_ok=True)

    # Save Python script
    script_path = os.path.join(project_folder, f"{project_name}.py")
    with open(script_path, 'w') as f:
        f.write(output)

    # Create and save README.md
    readme_content = create_documentation(project_name, output)
    readme_path = os.path.join(project_folder, "README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"Files created in {project_folder}")
    return True

def test_project(project_name):
    project_folder = os.path.join("projects", project_name)
    script_path = os.path.join(project_folder, f"{project_name}.py")
    
    if os.path.exists(script_path):
        print(f"Project {project_name} created successfully.")
        print(f"You can run {script_path} to test it.")
        return True
    else:
        print(f"Error: {project_name}.py not found in {project_folder}")
        return False

def improve_project(project_name, feedback):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    project_folder = os.path.join("projects", project_name)
    
    with open(os.path.join(project_folder, f"{project_name}.py"), 'r') as f:
        python_content = f.read()

    prompt = f"""
    Based on the following feedback, improve the Python project:
    
    Feedback: {feedback}
    
    Current Python code:
    {python_content}
    
    Provide an improved version of the Python code.
    You may include additional explanations or context if necessary.
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a Python development expert. Improve the given project based on the feedback."},
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
    # if create_and_save_files(final_output, project_name):
    #     if test_project(project_name):
    #         user_feedback = input("Do you want to improve the project? (yes/no): ")
    #         if user_feedback.lower() == 'yes':
    #             feedback = input("Please provide your feedback: ")
    #             if improve_project(project_name, feedback):
    #                 print(f"Project {project_name} has been improved based on your feedback.")
    #             else:
    #                 print("Failed to improve the project.")
    #     else:
    #         print("Project creation failed.")
    # else:
    #     print("Failed to create project files.")

    if create_and_save_files(final_output, project_name):
        if test_project(project_name):
            while True:
                user_feedback = input("Do you want to improve the project? (yes/no): ")
                if user_feedback.lower() == 'yes':
                    feedback = input("Please provide your feedback: ")
                    if improve_project(project_name, feedback):
                        print(f"Project {project_name} has been improved based on your feedback.")
                    else:
                        print("Failed to improve the project.")
                elif user_feedback.lower() == 'no':
                    print("No further improvements requested.")
                    break
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
        else:
            print("Project creation failed.")
    else:
        print("Failed to create project files.")


def main():
    try:
        query = input("Enter your query (e.g., 'create a simple calculator'): ")
        process_query(query)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please ensure all required packages are installed and up-to-date.")

if __name__ == "__main__":
    main()