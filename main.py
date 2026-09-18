import hashlib

import streamlit as st
from dotenv import load_dotenv

from utils.ats_analyzer import ATSAnalyzerError, analyze_ats
from utils.document_parser import DocumentParsingError, extract_resume_text
from utils.resume_parser import ResumeParserError, parse_resume

load_dotenv()

st.set_page_config(page_title="AI Resume & Job Match Assistant", page_icon="📄", layout="wide")
st.title("AI Resume & Job Match Assistant")
st.caption("Upload a PDF or DOCX resume to extract its text and generate structured resume data.")


@st.cache_data(show_spinner=False)
def get_resume_text(file_name, file_bytes):
    """Cache extraction only; this function never calls the LLM."""
    from io import BytesIO

    uploaded_copy = BytesIO(file_bytes)
    uploaded_copy.name = file_name
    return extract_resume_text(uploaded_copy)


def display_ats_analysis(resume, resume_text):
    """Display and trigger the ATS-style review without reparsing the resume."""
    st.caption("This is an application-defined heuristic score, not a score from an external ATS or a hiring prediction.")
    if st.button("Run ATS-Style Analysis", type="primary"):
        with st.spinner("Running ATS-style checks..."):
            try:
                st.session_state.ats_analysis = analyze_ats(resume, resume_text)
            except ATSAnalyzerError as exc:
                st.error(str(exc))

    analysis = st.session_state.get("ats_analysis")
    if not analysis:
        st.info("Run the analysis to view transparent, resume-specific feedback.")
        return

    st.subheader("ATS-STYLE SCORE")
    st.metric("Heuristic application score", f"{analysis['overall_score']} / 100")
    st.progress(analysis["overall_score"] / 100)

    st.subheader("Category scores")
    rows = []
    for category, score in analysis["category_scores"].items():
        maximum = analysis["category_maximums"][category]
        label = category.replace("_", " ").title()
        rows.append({"Category": label, "Score": f"{score}/{maximum}", "Percent": f"{score / maximum:.0%}"})
    st.table(rows)
    category_items = list(analysis["category_scores"].items())
    for start in range(0, len(category_items), 3):
        for column, (category, score) in zip(st.columns(3), category_items[start:start + 3]):
            maximum = analysis["category_maximums"][category]
            with column:
                st.metric(category.replace("_", " ").title(), f"{score / maximum:.0%}")
                st.progress(score / maximum)

    left, right = st.columns(2)
    with left:
        st.subheader("Strengths")
        if analysis["strengths"]:
            for strength in analysis["strengths"]:
                st.write(f"[OK] {strength}")
        else:
            st.write("No specific strengths were identified yet.")
    with right:
        st.subheader("Issues and recommendations")
        if analysis["issues"]:
            for issue, recommendation in zip(analysis["issues"], analysis["recommendations"]):
                with st.expander(f"[!] {issue}"):
                    st.write(recommendation)
        else:
            st.write("No programmatic issues were found.")
    if analysis["llm_feedback_error"]:
        st.info(analysis["llm_feedback_error"])


def display_resume(resume, resume_text):
    metrics = st.columns(4)
    metrics[0].metric("Skills", len(resume["skills"]))
    metrics[1].metric("Experience", len(resume["experience"]))
    metrics[2].metric("Projects", len(resume["projects"]))
    metrics[3].metric("Certifications", len(resume["certifications"]))

    overview, experience, skills, education, projects, certifications, ats, raw_json = st.tabs(
        ["Overview", "Experience", "Skills", "Education", "Projects", "Certifications", "ATS Analysis", "Raw JSON"]
    )
    with overview:
        personal = resume["personal_info"]
        st.subheader(personal["name"] or "Resume overview")
        contact = [value for key, value in personal.items() if key != "name" and value]
        if contact:
            st.write(" • ".join(contact))
        if resume["summary"]:
            st.write(resume["summary"])
        elif not contact:
            st.info("No personal details or summary were found.")
    with experience:
        if not resume["experience"]:
            st.info("No experience found.")
        for item in resume["experience"]:
            title = " — ".join(part for part in (item["role"], item["company"]) if part) or "Experience"
            with st.expander(title):
                st.write(" | ".join(part for part in (item["location"], item["start_date"], item["end_date"]) if part))
                for bullet in item["description"]:
                    st.write(f"• {bullet}")
    with skills:
        st.write(resume["skills"] or "No skills found.")
    with education:
        if not resume["education"]:
            st.info("No education found.")
        for item in resume["education"]:
            with st.expander(item["degree"] or item["institution"] or "Education"):
                st.write(item)
    with projects:
        if not resume["projects"]:
            st.info("No projects found.")
        for item in resume["projects"]:
            with st.expander(item["name"] or "Project"):
                st.write(item["description"])
                st.write("Technologies:", ", ".join(item["technologies"]) or "Not listed")
    with certifications:
        st.write(resume["certifications"] or "No certifications found.")
    with ats:
        display_ats_analysis(resume, resume_text)
    with raw_json:
        st.json(resume)


uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    file_key = hashlib.sha256(file_bytes).hexdigest()
    if st.session_state.get("resume_file_key") != file_key:
        st.session_state.resume_file_key = file_key
        st.session_state.pop("parsed_resume", None)
        st.session_state.pop("ats_analysis", None)

    try:
        resume_text = get_resume_text(uploaded_file.name, file_bytes)
    except DocumentParsingError as exc:
        st.error(str(exc))
        st.stop()

    st.subheader("Resume Preview")
    if not resume_text:
        st.warning("No readable text was found. Try a text-based PDF or DOCX document.")
    else:
        st.text_area("Extracted resume text", value=resume_text, height=320, disabled=True)
        if st.button("Parse Resume", type="primary"):
            with st.spinner("Extracting structured resume information..."):
                try:
                    st.session_state.parsed_resume = parse_resume(resume_text)
                    st.session_state.pop("ats_analysis", None)
                except ResumeParserError as exc:
                    st.error(str(exc))

    if st.session_state.get("parsed_resume"):
        st.divider()
        st.subheader("Structured Resume")
        display_resume(st.session_state.parsed_resume, resume_text)
