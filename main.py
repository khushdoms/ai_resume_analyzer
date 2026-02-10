import os
import re
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from groq import Groq
import docx2txt

# Load environment variables
load_dotenv()

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Streamlit config
st.set_page_config(page_title="Resume Analyzer", page_icon="📄", layout="wide")
st.title("Resume Analyzer")
st.markdown(
    "Upload your resume (PDF or Word) and get a **summary, key skills score and improvement suggestions**"
)

# File uploader (PDF + DOCX)
uploaded_file = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"]
)

# -------- TEXT EXTRACTION FUNCTIONS -------- #

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def extract_text_from_docx(file):
    file.seek(0)   
    text = docx2txt.process(file)

    return text


# -------- MAIN LOGIC -------- #

if uploaded_file:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    elif file_name.endswith(".docx"):
        text = extract_text_from_docx(uploaded_file)
    else:
        st.error("Unsupported file format")
        st.stop()

    # Clean text
    text_clean = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Resume Preview")
        st.text_area("Resume Text", value=text_clean, height=400)

    with col2:
        st.subheader("AI Analysis")

        if st.button("Analyze Resume"):
            with st.spinner("Analyzing resume..."):

                prompt = f"""
You are a resume expert.
Analyze the following resume provide:
1. Summary
2. List of key skills
3. Suggestions for improvement
4. A score out of 100 based on
- Skills match (30 points)
- Experience & achievement (30 points)
- Clarity & formatting (20 points)
- Overall presentation (20 points)

Resume:
{text_clean}

Provide the score breakdown in JSON format at the end starting with "Score JSON:"
"""

                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=700
                )

                result = response.choices[0].message.content

                parts = result.split("Score JSON:")
                analysis_text = parts[0]
                st.write(analysis_text)

                if len(parts) > 1:
                    try:
                        score_data = json.loads(parts[1].strip())

                        st.subheader("Score Breakdown")
                        df = pd.DataFrame({
                            "Category": list(score_data.keys()),
                            "Score": list(score_data.values())
                        })
                        st.bar_chart(df.set_index("Category"))

                        st.subheader("Overall Score")
                        total_score = sum(score_data.values())
                        st.progress(min(total_score / 100, 1.0))

                    except Exception:
                        st.warning("Could not parse score JSON")