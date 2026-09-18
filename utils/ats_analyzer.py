"""Deterministic ATS-style resume checks with optional Groq feedback."""

import json
import os
import re

from groq import Groq

from utils.prompts import ATS_FEEDBACK_PROMPT


CATEGORY_MAXIMUMS = {
    "section_completeness": 20,
    "contact_information": 10,
    "keyword_quality": 20,
    "experience_quality": 25,
    "resume_structure": 15,
    "content_clarity": 10,
}

ACTION_WORDS = {
    "achieved", "built", "created", "delivered", "designed", "developed", "implemented",
    "improved", "increased", "launched", "led", "managed", "optimized", "reduced",
    "streamlined", "supported", "tested", "automated", "collaborated", "deployed",
}
GENERIC_SKILLS = {
    "communication", "hard working", "hardworking", "leadership", "motivated", "team player",
    "teamwork", "problem solving", "time management", "ms office", "microsoft office",
}
GENERIC_SUMMARY_PHRASES = {
    "hardworking", "highly motivated", "results-driven", "team player", "quick learner",
    "seeking a challenging", "dynamic professional",
}


class ATSAnalyzerError(Exception):
    """Raised when ATS analysis cannot begin due to invalid input."""


def _normalise(value):
    return re.sub(r"\s+", " ", value.strip().lower()) if isinstance(value, str) else ""


def _bullets(resume_data):
    return [
        bullet.strip()
        for entry in resume_data.get("experience", [])
        if isinstance(entry, dict)
        for bullet in entry.get("description", [])
        if isinstance(bullet, str) and bullet.strip()
    ]


def _has_action_word(text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    return bool(words & ACTION_WORDS)


def _has_measurement(text):
    return bool(re.search(r"\b\d+(?:[,.]\d+)?\s*(?:%|\+|x\b|hours?|days?|weeks?|months?|years?|users?|clients?|projects?|team members?)", text, re.I))


def _contains_skill(text, skill):
    skill = _normalise(skill)
    if len(skill) < 2:
        return False
    return re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text) is not None


def _add_issue(issues, recommendations, issue, recommendation):
    if issue not in issues:
        issues.append(issue)
        recommendations.append(recommendation)


def _programmatic_analysis(resume_data, resume_text):
    """Calculate all score components from transparent, local checks."""
    scores = {key: 0 for key in CATEGORY_MAXIMUMS}
    strengths, issues, recommendations = [], [], []
    personal = resume_data.get("personal_info", {}) if isinstance(resume_data.get("personal_info"), dict) else {}

    sections = (
        ("summary", 3, bool(resume_data.get("summary"))),
        ("skills", 4, bool(resume_data.get("skills"))),
        ("experience", 5, bool(resume_data.get("experience"))),
        ("education", 4, bool(resume_data.get("education"))),
        ("projects", 2, bool(resume_data.get("projects"))),
        ("certifications", 2, bool(resume_data.get("certifications"))),
    )
    scores["section_completeness"] = sum(points for _, points, present in sections if present)
    missing_sections = [name.title() for name, _, present in sections if not present]
    if not missing_sections:
        strengths.append("All core resume sections are present.")
    else:
        _add_issue(issues, recommendations, f"Missing or empty sections: {', '.join(missing_sections)}.", "Add the missing sections when they reflect real qualifications or experience.")

    contact_weights = {"name": 2, "email": 2, "phone": 2, "location": 1, "linkedin": 1, "github": 2}
    scores["contact_information"] = sum(points for field, points in contact_weights.items() if _normalise(personal.get(field)))
    contact_labels = {"name": "Name", "email": "Email", "phone": "Phone", "location": "Location", "linkedin": "LinkedIn", "github": "GitHub"}
    missing_contact = [contact_labels[field] for field in contact_weights if not _normalise(personal.get(field))]
    if not missing_contact:
        strengths.append("Contact information is complete.")
    else:
        _add_issue(issues, recommendations, f"Missing contact information: {', '.join(missing_contact)}.", "Add accurate contact details that you want recruiters to use, including relevant professional profile links.")

    skills = [skill for skill in resume_data.get("skills", []) if isinstance(skill, str) and skill.strip()]
    normalised_skills = [_normalise(skill) for skill in skills]
    duplicate_skills = sorted({skill for skill in normalised_skills if normalised_skills.count(skill) > 1})
    generic_skills = [skill for skill in skills if _normalise(skill) in GENERIC_SKILLS]
    if len(skills) >= 8:
        scores["keyword_quality"] += 8
        strengths.append("A strong technical skills section is present.")
    elif skills:
        scores["keyword_quality"] += 3 if len(skills) <= 3 else 6
        _add_issue(issues, recommendations, "The skills section contains only a few skills.", "Add relevant tools, technologies, and domain skills that are already supported by your experience.")
    else:
        _add_issue(issues, recommendations, "No skills section was found.", "Add a concise, clearly labelled skills section using skills demonstrated in the resume.")
    if skills and not duplicate_skills:
        scores["keyword_quality"] += 4
    elif duplicate_skills:
        _add_issue(issues, recommendations, f"Duplicate skills found: {', '.join(duplicate_skills)}.", "Keep each skill once and use the extra space for more specific, relevant skills.")
    if skills and len(generic_skills) * 2 <= len(skills):
        scores["keyword_quality"] += 4
    elif generic_skills:
        _add_issue(issues, recommendations, "The skills section relies heavily on generic skills.", "Prioritize concrete tools, technologies, methods, or domain skills over broad soft-skill labels.")

    experience_text = " ".join(
        " ".join([entry.get("role", ""), entry.get("company", "")] + entry.get("description", []))
        for entry in resume_data.get("experience", []) if isinstance(entry, dict)
    ).lower()
    matched_skills = [skill for skill in skills if _contains_skill(experience_text, skill)]
    if experience_text and matched_skills:
        scores["keyword_quality"] += 4
    elif skills and experience_text:
        _add_issue(issues, recommendations, "Skills are not clearly connected to experience descriptions.", "Mention relevant technologies or methods in the work where you actually used them.")

    experience_entries = [entry for entry in resume_data.get("experience", []) if isinstance(entry, dict)]
    bullet_points = _bullets(resume_data)
    if len(experience_entries) >= 2:
        scores["experience_quality"] += 7
        strengths.append("Work experience has multiple entries.")
    elif experience_entries:
        scores["experience_quality"] += 4
    else:
        _add_issue(issues, recommendations, "No work experience entries were found.", "Add work experience entries with truthful roles, employers, dates, and accomplishments when applicable.")
    if len(bullet_points) >= 8:
        scores["experience_quality"] += 6
    elif len(bullet_points) >= 4:
        scores["experience_quality"] += 4
    elif bullet_points:
        scores["experience_quality"] += 2
        _add_issue(issues, recommendations, "Experience has very few descriptive bullet points.", "Add concise bullets that explain your real responsibilities, tools, and outcomes.")
    if bullet_points:
        action_ratio = sum(_has_action_word(bullet) for bullet in bullet_points) / len(bullet_points)
        scores["experience_quality"] += 5 if action_ratio >= 0.6 else 3 if action_ratio >= 0.3 else 1
        if action_ratio < 0.6:
            _add_issue(issues, recommendations, "Several experience bullets lack action-oriented language.", "Start factual bullets with an action verb, then describe the task or technology and the real result.")
        metric_ratio = sum(_has_measurement(bullet) for bullet in bullet_points) / len(bullet_points)
        scores["experience_quality"] += 5 if metric_ratio >= 0.4 else 3 if metric_ratio >= 0.15 else 1 if metric_ratio else 0
        if not metric_ratio:
            _add_issue(issues, recommendations, "Experience bullets do not show measurable achievements.", "Where you have real evidence, add specific outcomes such as scope, time saved, volume, percentage, or number of users. Do not invent metrics.")
        substantial_ratio = sum(len(bullet.split()) >= 7 for bullet in bullet_points) / len(bullet_points)
        scores["experience_quality"] += 2 if substantial_ratio >= 0.75 else 1 if substantial_ratio >= 0.4 else 0
        if substantial_ratio < 0.4:
            _add_issue(issues, recommendations, "Several experience descriptions are too short to show impact.", "Expand short bullets with the relevant task, technology, and factual outcome.")

    word_count = len(re.findall(r"\b\w+\b", resume_text))
    scores["resume_structure"] += 4 if word_count >= 250 else 3 if word_count >= 150 else 1 if word_count >= 75 else 0
    present_section_count = len(sections) - len(missing_sections)
    scores["resume_structure"] += round(present_section_count * 4 / len(sections))
    if bullet_points:
        scores["resume_structure"] += 3 if all(len(bullet.split()) >= 4 for bullet in bullet_points) else 1
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    if lines:
        readable_ratio = sum(len(line) <= 160 for line in lines) / len(lines)
        scores["resume_structure"] += 2 if readable_ratio >= 0.9 else 1 if readable_ratio >= 0.7 else 0
    if scores["resume_structure"] >= 12:
        strengths.append("Resume structure is easy to scan.")

    summary = _normalise(resume_data.get("summary"))
    if summary:
        generic_summary = any(phrase in summary for phrase in GENERIC_SUMMARY_PHRASES)
        summary_words = len(summary.split())
        scores["content_clarity"] += 5 if summary_words >= 20 and not generic_summary else 3 if summary_words >= 10 else 1
        if generic_summary or summary_words < 10:
            _add_issue(issues, recommendations, "The summary is generic or too brief.", "State your actual role, strongest relevant skills, and the type of work you have done; avoid unsupported claims.")
    if bullet_points:
        average_words = sum(len(bullet.split()) for bullet in bullet_points) / len(bullet_points)
        scores["content_clarity"] += 3 if average_words >= 8 else 2 if average_words >= 5 else 1
    if skills and not duplicate_skills and len(generic_skills) * 2 <= len(skills):
        scores["content_clarity"] += 2

    for category, maximum in CATEGORY_MAXIMUMS.items():
        scores[category] = min(maximum, max(0, int(scores[category])))
    return scores, strengths, issues, recommendations


def _parse_feedback(response):
    """Validate the small JSON object returned by the qualitative feedback request."""
    candidate = response.strip() if isinstance(response, str) else ""
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.I | re.S)
    if fenced:
        candidate = fenced.group(1)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", candidate):
        try:
            data, _ = decoder.raw_decode(candidate[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            strengths = [item.strip() for item in data.get("strengths", []) if isinstance(item, str) and item.strip()]
            feedback = [item for item in data.get("feedback", []) if isinstance(item, dict)]
            return strengths, feedback
    raise ValueError("Invalid JSON feedback")


def _llm_feedback(resume_data, resume_text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return [], [], "Groq feedback was skipped because GROQ_API_KEY is missing. The ATS-style score is still available."
    try:
        response = Groq(api_key=api_key).chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": ATS_FEEDBACK_PROMPT.replace("{resume_json}", json.dumps(resume_data)).replace("{resume_text}", resume_text)}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1200,
        )
        strengths, feedback = _parse_feedback(response.choices[0].message.content)
        issues, recommendations = [], []
        for item in feedback:
            issue, recommendation = item.get("issue"), item.get("recommendation")
            if isinstance(issue, str) and issue.strip() and isinstance(recommendation, str) and recommendation.strip():
                issues.append(issue.strip())
                recommendations.append(recommendation.strip())
        return strengths, list(zip(issues, recommendations)), ""
    except Exception:
        return [], [], "Groq qualitative feedback was unavailable. The ATS-style score uses the completed programmatic checks."


def analyze_ats(resume_data, resume_text):
    """Return an application-defined ATS-style assessment for parsed resume data."""
    if not isinstance(resume_data, dict):
        raise ATSAnalyzerError("Parse a resume before starting ATS-style analysis.")
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ATSAnalyzerError("There is no readable resume text available for ATS-style analysis.")
    scores, strengths, issues, recommendations = _programmatic_analysis(resume_data, resume_text)
    llm_strengths, llm_feedback, feedback_error = _llm_feedback(resume_data, resume_text)
    strengths.extend(item for item in llm_strengths if item not in strengths)
    for issue, recommendation in llm_feedback:
        _add_issue(issues, recommendations, issue, recommendation)
    return {
        "overall_score": sum(scores.values()),
        "category_scores": scores,
        "category_maximums": CATEGORY_MAXIMUMS,
        "strengths": strengths,
        "issues": issues,
        "recommendations": recommendations,
        "llm_feedback_error": feedback_error,
    }
