# AI Resume & Job Match Assistant

Phase 2 of a Streamlit and Groq-powered resume assistant. It extracts resumes into structured JSON and provides a transparent ATS-style heuristic review. It does not yet match jobs, generate interviews, or rewrite resumes.

## Features

- PDF and DOCX resume upload
- Resume text extraction and whitespace cleaning
- AI-powered resume parsing with Groq
- Structured resume JSON without invented fields
- Resume overview dashboard for experience, skills, education, projects, and certifications
- ATS-style resume analysis with transparent category scores and recommendations

## Architecture

```text
PDF/DOCX
   ↓
Document Parser
   ↓
Clean Text
   ↓
Groq LLM
   ↓
Structured Resume JSON
   ↓
ATS Analyzer
   ↓
Programmatic Checks + one optional Groq clarity review
   ↓
ATS-Style Score
   ↓
Streamlit Dashboard
```

## Setup and run

```bash
git clone https://github.com/khushdoms/ai_resume_analyzer.git
cd ai_resume_analyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Then start the app:

```bash
streamlit run main.py
```

Upload a PDF or DOCX file, review the extracted text, then select **Parse Resume**. The API is called only after that button click; structured data remains available for the current Streamlit session.

Open **ATS Analysis** and select **Run ATS-Style Analysis** to review the parsed resume. This reuses the current structured resume data; it does not parse the document again.

## ATS-style scoring methodology

The score is an application-defined heuristic out of 100, not a score from Workday, LinkedIn, another ATS, or a prediction of hiring success.

| Component | Maximum | Checks |
| --- | ---: | --- |
| Section completeness | 20 | Summary, skills, experience, education, projects, certifications |
| Contact information | 10 | Name, email, phone, location, LinkedIn, GitHub |
| Keyword/skill quality | 20 | Skill count, duplicates, specificity, use in experience |
| Experience quality | 25 | Entries, bullets, action verbs, factual measurable outcomes, detail |
| Resume structure | 15 | Content length, section coverage, readable lines, bullet structure |
| Content clarity | 10 | Summary specificity and descriptive bullet clarity |

All points are calculated locally from the parsed resume and extracted text. Groq receives one separate, optional request for qualitative clarity feedback only; it does not create or alter the score. If the API key is unavailable or that request fails, the deterministic score remains available.

## Current scope

This phase intentionally excludes job-description matching, job-specific keyword gaps, resume rewriting, interview questions, RAG/vector databases, authentication, and databases. Those belong to later phases.
