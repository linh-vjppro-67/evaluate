import streamlit as st
import json
import os
import requests
from collections import defaultdict

# Use secrets to access API_KEY and ENDPOINT
API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]

def generate_default_prompt(file_path):
    """Generates the default prompt based on the contents of the data.json file"""
    # Read the data.json file
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

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

        # Group correct and incorrect responses by skill
        skill_list = entry['skills']
        if entry['isCorrectAnswer']:
            for skill in skill_list:
                correct_responses[skill].append(entry['content'])
        else:
            for skill in skill_list:
                incorrect_responses[skill].append(entry['content'])

    # Generate structured prompt
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

    return prompt


def analyze_candidate_responses(custom_prompt):
    """Sends a summary request to OpenAI API with the custom prompt"""
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

        # Return the result
        return analysis

    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing the responses: {e}")
        return None


def main():
    # Streamlit UI layout
    st.title("Candidate Response Analysis")
    st.write("This app analyzes candidate responses based on the default `data.json` file.")
    
    # Default file path
    file_path = './data.json'

    # Check if the file exists
    if os.path.exists(file_path):
        # Generate the default prompt based on the content of the file
        default_prompt = generate_default_prompt(file_path)
    else:
        st.error(f"The file `{file_path}` does not exist in the current directory.")
        return

    # Allow user to modify the prompt
    custom_prompt = st.text_area("Edit the AI prompt for analysis:", default_prompt, height=300)

    # Provide a button to start the analysis
    if st.button("Analyze"):
        with st.spinner("Analyzing responses..."):
            analysis_result = analyze_candidate_responses(custom_prompt)
            if analysis_result:
                st.subheader("Analysis Result:")
                st.write(analysis_result)


if __name__ == "__main__":
    main()
