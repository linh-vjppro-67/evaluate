import json
import os
import requests
from collections import defaultdict
import streamlit as st

# Get API credentials from st.secrets
API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]

def analyze_candidate_responses(file_path, prompt):
    """Processes the data.json file and sends a summary request to OpenAI API"""
    
    # Read the data.json file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        st.error(f"File not found at the path: {file_path}")
        return None

    # Collect general information
    job_titles = set()
    categories = set()
    skills = set()
    correct_responses = defaultdict(list)
    incorrect_responses = defaultdict(list)

    # Process each response
    for entry in data:
        job_titles.add(entry['jobTitle'])
        categories.update(entry['categories'])
        skills.update(entry['skills'])

        # Group correct and incorrect responses by skill and question content
        skill_list = entry['skills']
        question = entry['content']  # question text
        if entry['isCorrectAnswer']:
            for skill in skill_list:
                correct_responses[skill].append(question)
        else:
            for skill in skill_list:
                incorrect_responses[skill].append(question)

    # Add the user-provided prompt to the API request
    prompt = f"""
    Based on the candidate's responses, analyze their overall strengths and gaps.

    **Job Titles:** {', '.join(job_titles)}  
    **Skill Categories:** {', '.join(categories)}  
    **Skills Assessed:** {', '.join(skills)}

    ### **Instructions for AI:**  
    - Summarize the candidate’s **Strengths**: areas where they performed well.  
    - Summarize the candidate’s **Gaps**: areas where improvement is needed.  
    - Focus on skill-level insights, **do NOT** generate a separate strength/gap for each individual question.  

    ### **Questions Candidate Answered Correctly:**  
    {json.dumps(correct_responses, ensure_ascii=False, indent=2)}

    ### **Questions Candidate Answered Incorrectly:**  
    {json.dumps(incorrect_responses, ensure_ascii=False, indent=2)}

    ### **Expected Output Format (markdown):**
    **Strengths:**  
    - Well-versed in [Skill A]  
    - Strong understanding of [Skill B]  
    - Proficient in applying [Skill C]  

    **Gaps:**  
    - Needs improvement in [Skill X]  
    - Struggles with [Skill Y]  
    - Requires more practice in [Skill Z]
    """

    # API request payload
    payload = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant analyzing a candidate's skill assessment."},
            {"role": "user", "content": custom_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.9
    }

    headers = {
        'Content-Type': 'application/json',
        'api-key': API_KEY
    }

    try:
        # Send request to OpenAI API
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

        return analysis

    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing the responses: {e}")
        return None

# Streamlit UI
# Streamlit UI
st.title("Candidate Skill Assessment Analysis")

# Hardcoded path to the local file
file_path = './data.json'

if os.path.exists(file_path):
    st.write("File found! Ready to analyze the responses.")

    # Define the default prompt text (pre-filled in the input)
    default_prompt = """
    Based on the candidate's responses, analyze their overall strengths and gaps.

    **Job Titles:** {job_titles}  
    **Skill Categories:** {categories}  
    **Skills Assessed:** {skills}

    ### **Instructions for AI:**  
    - Summarize the candidate’s **Strengths**: areas where they performed well.  
    - Summarize the candidate’s **Gaps**: areas where improvement is needed.  
    - Focus on skill-level insights, **do NOT** generate a separate strength/gap for each individual question.  

    ### **Questions Candidate Answered Correctly:**  
    {correct_responses}

    ### **Questions Candidate Answered Incorrectly:**  
    {incorrect_responses}

    ### **Expected Output Format (markdown):**
    **Strengths:**  
    - Well-versed in [Skill A]  
    - Strong understanding of [Skill B]  
    - Proficient in applying [Skill C]  

    **Gaps:**  
    - Needs improvement in [Skill X]  
    - Struggles with [Skill Y]  
    - Requires more practice in [Skill Z]
    """

    # Input for custom prompt (default text can be modified by the user)
    custom_prompt = st.text_area("Edit the prompt (default is provided below):", default_prompt, height=250)

    # Button to trigger analysis
    if st.button("Analyze"):
        st.write("Analyzing...")

        # If the user has modified the input, use their custom prompt; otherwise, use the default one
        prompt_to_use = custom_prompt

        # Call the function to analyze the responses, passing in the appropriate prompt
        analysis = analyze_candidate_responses(file_path, prompt_to_use)

        if analysis:
            st.subheader("Analysis Result:")
            st.markdown(analysis)
            # Optionally, save the result to a file
            with open("overall_analysis.txt", "w", encoding="utf-8") as f:
                f.write(analysis)
            st.download_button(
                label="Download Analysis",
                data=open("overall_analysis.txt", "r").read(),
                file_name="overall_analysis.txt",
                mime="text/plain"
            )
        else:
            st.warning("No analysis result available.")
else:
    st.error(f"The file {file_path} does not exist. Please check the path.")
