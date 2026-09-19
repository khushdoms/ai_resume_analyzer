# 📄 AI Resume & Job Match Assistant

An AI-powered resume analysis application built with **Python, Streamlit, and Groq LLMs**.

The application extracts information from PDF/DOCX resumes, converts the resume into structured JSON, and performs an **ATS-style resume analysis** using transparent, application-defined scoring rules.

> 🔜 Job Description Matching, Resume Improvement, and Interview Preparation are planned for future phases.

---

## 🚀 What This Project Does

Most resume analyzers simply send the entire resume to an LLM and ask for feedback.

This project takes a more structured approach:

```text
Resume PDF / DOCX
        ↓
Document Text Extraction
        ↓
Text Cleaning
        ↓
AI Resume Parsing
        ↓
Structured Resume JSON
        ↓
Programmatic ATS Analysis
        ↓
Optional AI Clarity Feedback
        ↓
ATS-Style Score + Recommendations
```

The goal is to combine **traditional Python-based analysis** with **Generative AI** instead of relying entirely on an LLM to make decisions.

---

# ✨ Features

## Phase 1 — Resume Parser

### 📁 PDF & DOCX Support

Upload a resume in either:

* PDF
* DOCX

The application extracts readable text from the uploaded document.

### 🧹 Resume Text Cleaning

The extracted text is cleaned before analysis.

The parser:

* Normalizes whitespace
* Removes unnecessary blank lines
* Preserves useful line and paragraph structure
* Handles extraction errors
* Detects unsupported file formats

---

### 🤖 AI-Powered Resume Parsing

The extracted resume text is sent to a Groq-hosted LLM.

Instead of asking the model for a general paragraph of feedback, the application asks the model to convert the resume into a predefined JSON structure.

For example:

```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1 1234567890",
    "location": "New York",
    "linkedin": "",
    "github": ""
  },
  "summary": "...",
  "skills": [
    "Python",
    "AWS",
    "React"
  ],
  "experience": [],
  "education": [],
  "projects": [],
  "certifications": []
}
```

The model is explicitly instructed to:

* Extract only information present in the resume
* Never invent information
* Follow the defined schema
* Use empty values when information is missing
* Preserve factual resume content

---

## Phase 2 — ATS-Style Resume Analyzer

The application analyzes the structured resume using **local, deterministic checks**.

The ATS-style score is calculated by the application rather than simply asking the LLM:

> "Give this resume a score out of 100."

This makes the scoring process more transparent and easier to understand.

### ATS Score Categories

| Category                | Maximum Score |
| ----------------------- | ------------: |
| Section Completeness    |            20 |
| Contact Information     |            10 |
| Keyword / Skill Quality |            20 |
| Experience Quality      |            25 |
| Resume Structure        |            15 |
| Content Clarity         |            10 |
| **Total**               |       **100** |

---

### 📊 Section Completeness

Checks whether important resume sections are present:

* Summary
* Skills
* Experience
* Education
* Projects
* Certifications

---

### 👤 Contact Information

Checks for:

* Name
* Email
* Phone
* Location
* LinkedIn
* GitHub

---

### 🛠 Keyword & Skill Quality

The analyzer checks:

* Number of skills
* Duplicate skills
* Generic skills
* Whether skills appear in experience descriptions
* Whether the skills section contains useful technical/domain skills

---

### 💼 Experience Quality

The analyzer evaluates the available experience information.

It checks:

* Number of experience entries
* Number of descriptive bullets
* Action-oriented language
* Measurable achievements
* Description length
* Whether bullets provide useful detail

For example, a bullet such as:

> Developed a custom WooCommerce plugin.

contains an action-oriented description but does not provide a measurable result.

The application can therefore recommend adding a real measurable outcome when one exists.

**It never invents metrics.**

---

### 📐 Resume Structure

The application checks characteristics such as:

* Resume content length
* Section coverage
* Bullet structure
* Readability of extracted lines

---

### ✍️ Content Clarity

The application checks:

* Summary length
* Generic summary language
* Description quality
* Average bullet length

---

# 🤖 Where Generative AI Is Used

The project deliberately does **not** use the LLM for everything.

### Groq LLM is used for:

1. Structured resume extraction
2. Qualitative resume clarity feedback

### Python/programmatic logic is used for:

1. Section completeness
2. Contact information checks
3. Skill checks
4. Duplicate detection
5. Generic skill detection
6. Experience analysis
7. Action-word analysis
8. Measurement detection
9. Resume structure checks
10. Final ATS-style score calculation

This creates a hybrid architecture:

```text
                Resume
                   │
                   ▼
          Document Extraction
                   │
                   ▼
             Clean Text
                   │
                   ▼
              Groq LLM
                   │
                   ▼
        Structured Resume JSON
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   Python Analysis      Groq Feedback
          │                 │
          └────────┬────────┘
                   ▼
          ATS-Style Dashboard
```

---

# 🧠 Why Structured JSON?

A major design decision in this project is converting the resume into structured data before performing further analysis.

Instead of working with:

```text
John Doe
john@example.com

Experience:
Software Developer...
...
Skills:
Python...
...
```

the application works with:

```text
{
    "personal_info": {...},
    "skills": [...],
    "experience": [...],
    "education": [...],
    "projects": [...]
}
```

This makes the data easier to:

* Analyze
* Validate
* Display
* Score
* Compare with future job descriptions
* Reuse for future AI features

This structured representation will also be used by future phases of the project.

---

# 🏗️ Project Architecture

```text
ai_resume_analyzer/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── utils/
    ├── __init__.py
    ├── document_parser.py
    ├── resume_parser.py
    ├── ats_analyzer.py
    └── prompts.py
```

### `main.py`

Main Streamlit application.

Responsible for:

* File upload
* Resume preview
* Streamlit UI
* Session state
* Resume parsing trigger
* ATS analysis trigger
* Dashboard rendering

---

### `utils/document_parser.py`

Responsible for document processing.

Main functions:

```python
extract_text_from_pdf()
extract_text_from_docx()
extract_resume_text()
clean_text()
```

---

### `utils/resume_parser.py`

Responsible for AI-powered resume parsing.

Main function:

```python
parse_resume()
```

It sends cleaned resume text to Groq and returns normalized structured resume data.

It also handles:

* Invalid JSON
* Markdown-wrapped JSON
* Missing API keys
* API errors
* Invalid model responses

---

### `utils/ats_analyzer.py`

Responsible for ATS-style analysis.

The analyzer contains the deterministic scoring logic.

It checks:

```text
Section completeness
Contact information
Keyword quality
Experience quality
Resume structure
Content clarity
```

It also optionally requests qualitative feedback from Groq.

---

### `utils/prompts.py`

Contains prompts used by the LLM.

Currently includes prompts for:

* Structured resume extraction
* ATS qualitative feedback

Keeping prompts separate makes them easier to maintain and explain.

---

# 🔄 Complete Application Flow

## Step 1 — Upload Resume

The user uploads:

```text
resume.pdf
```

or:

```text
resume.docx
```

---

## Step 2 — Extract Text

The document parser extracts readable text.

```text
PDF/DOCX
   ↓
PyPDF2 / python-docx
   ↓
Raw Text
```

---

## Step 3 — Clean Text

The application normalizes whitespace and removes unnecessary blank lines.

```text
Raw Text
   ↓
clean_text()
   ↓
Clean Resume Text
```

---

## Step 4 — Parse Resume with AI

When the user clicks:

**Parse Resume**

the cleaned text is sent to the Groq LLM.

```text
Resume Text
     ↓
Groq LLM
     ↓
Structured JSON
```

The structured result is stored in Streamlit session state.

---

## Step 5 — Display Structured Resume

The application displays:

* Overview
* Experience
* Skills
* Education
* Projects
* Certifications
* Raw JSON

It also displays basic metrics:

```text
Skills        Experience
Projects      Certifications
```

---

## Step 6 — Run ATS Analysis

The user opens:

**ATS Analysis**

and clicks:

**Run ATS-Style Analysis**

The application reuses the existing structured resume.

It does **not** parse the resume again.

---

## Step 7 — Programmatic Analysis

Python calculates the category scores.

```text
Resume JSON
    ↓
Local checks
    ↓
Category scores
    ↓
Overall score
```

---

## Step 8 — Optional AI Feedback

The application can send the resume information to Groq for qualitative clarity feedback.

The LLM provides:

* Strengths
* Issues
* Recommendations

The LLM does **not** determine or modify the ATS score.

---

## Step 9 — Final Dashboard

The user receives:

```text
ATS-STYLE SCORE

82 / 100
```

along with:

* Category scores
* Strengths
* Issues
* Recommendations

---

# ⚙️ Tech Stack

| Technology    | Purpose                                  |
| ------------- | ---------------------------------------- |
| Python        | Application logic                        |
| Streamlit     | Web interface                            |
| Groq          | LLM API                                  |
| GPT-OSS-120B  | AI resume parsing & qualitative feedback |
| PyPDF2        | PDF text extraction                      |
| python-docx   | DOCX text extraction                     |
| Pandas        | Data handling / visualization support    |
| python-dotenv | Environment variable management          |

---

# 🔐 Environment Setup

The project uses a Groq API key.

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit the `.env` file to GitHub.

---

# 💻 Installation

## 1. Clone the repository

```bash
git clone https://github.com/khushdoms/ai_resume_analyzer.git
cd ai_resume_analyzer
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Groq API

Create:

```text
.env
```

and add:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## 5. Run the application

```bash
streamlit run main.py
```

The Streamlit application will open in your browser.

---

# 📌 Usage

### 1. Upload your resume

Supported formats:

```text
PDF
DOCX
```

### 2. Review extracted text

The application shows the extracted resume text before sending it to the AI model.

### 3. Parse the resume

Click:

**Parse Resume**

The application creates structured resume data.

### 4. Review your resume

Explore:

* Overview
* Experience
* Skills
* Education
* Projects
* Certifications
* Raw JSON

### 5. Run ATS Analysis

Open:

**ATS Analysis**

and click:

**Run ATS-Style Analysis**

Review:

* Overall ATS-style score
* Category scores
* Strengths
* Issues
* Recommendations

---

# 📊 Example ATS Analysis

Example output:

```text
ATS-STYLE SCORE

82 / 100
```

Category analysis:

```text
Section Completeness      18 / 20
Contact Information        9 / 10
Keyword / Skill Quality   16 / 20
Experience Quality        21 / 25
Resume Structure          11 / 15
Content Clarity            7 / 10
```

The exact score depends on the uploaded resume.

---

# 🔒 Privacy

The application does not intentionally store uploaded resume files in a database.

Resume content is processed during the current Streamlit session.

When AI analysis is requested, resume content is sent to the configured Groq API for processing.

Do not upload sensitive information if you are not comfortable sending it to the configured AI provider.

---

# 🚧 Current Project Scope

### ✅ Completed

* [x] PDF resume upload
* [x] DOCX resume upload
* [x] Resume text extraction
* [x] Resume text cleaning
* [x] AI-powered resume parsing
* [x] Structured resume JSON
* [x] Resume overview dashboard
* [x] Experience extraction
* [x] Skills extraction
* [x] Education extraction
* [x] Project extraction
* [x] Certification extraction
* [x] ATS-style analysis
* [x] Transparent scoring methodology
* [x] Programmatic resume checks
* [x] AI qualitative feedback
* [x] Error handling
* [x] Session-based result reuse

---

# 🔜 Planned Features

The project will be expanded in future phases.

## Phase 3 — Job Description Matching

Planned functionality:

```text
Resume
   +
Job Description
   ↓
Job Requirement Extraction
   ↓
Skill Matching
   ↓
Keyword Gap Analysis
   ↓
Experience Matching
   ↓
Resume-to-Job Match Score
```

---

## Phase 4 — Resume Improvement

Planned functionality:

* AI resume summary improvement
* Experience bullet improvement
* Project description improvement
* Achievement analysis
* Keyword recommendations

The application will preserve factual information and will not invent experience or achievements.

---

## Phase 5 — Interview Preparation

Planned functionality:

* Resume-based interview questions
* Job-specific technical questions
* Project-based questions
* Behavioral questions
* AI interview practice

---

# 🧩 Future Architecture

The planned final application will evolve into:

```text
                    Resume
                       │
                       ▼
              Document Parser
                       │
                       ▼
             Structured Resume
                    JSON
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
       ATS         Job Match      Resume
     Analysis       Analysis     Improvement
          │            │             │
          └────────────┼─────────────┘
                       │
                       ▼
              Interview Preparation
```

---

# 🎯 Project Goals

This project is designed to demonstrate how a practical AI application can combine:

* Python
* Streamlit
* Document processing
* LLMs
* Structured JSON
* Prompt engineering
* Programmatic analysis
* AI-generated feedback

The goal is not simply to send a document to an LLM and display its response.

Instead, the project demonstrates a hybrid AI architecture where:

```text
LLM
+
Python
+
Structured Data
+
Deterministic Rules
```

work together to build a more reliable application.

---

# 📚 Learning Outcomes

By studying this project, developers can learn how to:

* Build an AI application with Python
* Process PDF and DOCX documents
* Extract structured information from unstructured text
* Design structured LLM prompts
* Work with JSON responses from LLMs
* Validate and normalize AI output
* Handle LLM/API errors
* Build Streamlit dashboards
* Use session state effectively
* Combine LLM reasoning with deterministic Python logic
* Build transparent scoring systems
* Design an incremental AI application architecture

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

If you find a bug or have an idea for a feature, feel free to open an issue or submit a pull request.

---
