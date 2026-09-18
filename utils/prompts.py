"""Prompts used by the resume parsing workflow."""

RESUME_PARSER_PROMPT = """
You are a precise resume information extraction system. Extract structured data from the resume below. Return ONLY one valid JSON object; do not use Markdown, code fences, prose, or comments.

Rules:
- Extract only facts explicitly present in the resume. Never infer or invent information.
- Use an empty string for a missing single value and an empty array for a missing list.
- Follow the schema exactly, including all keys.
- Normalize obvious whitespace and formatting issues, but preserve factual content.
- Keep each experience and project description item as a separate bullet-sized string where possible. Do not create unsupported bullets.
- Use strings for dates exactly as stated or lightly normalized; do not guess missing dates.

Required schema:
{
  "personal_info": {"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "github": ""},
  "summary": "", "skills": [],
  "experience": [{"company": "", "role": "", "location": "", "start_date": "", "end_date": "", "description": []}],
  "education": [{"degree": "", "institution": "", "location": "", "start_date": "", "end_date": ""}],
  "projects": [{"name": "", "description": [], "technologies": []}],
  "certifications": [{"name": "", "issuer": "", "date": ""}]
}

Resume text:
---
{resume_text}
---
""".strip()


ATS_FEEDBACK_PROMPT = """
You are reviewing a resume for clarity only. Use the supplied resume JSON and resume text.
Return ONLY valid JSON in this exact shape:
{"strengths": [""], "feedback": [{"issue": "", "recommendation": ""}]}

Rules:
- Do not give a score and do not estimate hiring likelihood.
- State only observations supported by the supplied resume.
- Do not invent achievements, skills, jobs, dates, or metrics.
- Return at most 3 strengths and 3 feedback items.
- Each feedback item needs a specific, useful recommendation.
- If no supported feedback is available, return empty arrays.

Parsed resume JSON:
{resume_json}

Resume text:
{resume_text}
""".strip()
