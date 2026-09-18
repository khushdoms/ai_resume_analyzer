"""Groq-powered structured resume parsing helpers."""

import json
import os
import re

from groq import Groq

from utils.prompts import RESUME_PARSER_PROMPT


class ResumeParserError(Exception):
    """Raised when structured resume data cannot be produced."""


def _empty_resume():
    return {
        "personal_info": {key: "" for key in ("name", "email", "phone", "location", "linkedin", "github")},
        "summary": "", "skills": [], "experience": [], "education": [], "projects": [], "certifications": [],
    }


def _string(value):
    return value.strip() if isinstance(value, str) else ""


def _string_list(value):
    return [_string(item) for item in value if isinstance(item, str) and _string(item)] if isinstance(value, list) else []


def _records(value, fields, list_fields=()):
    if not isinstance(value, list):
        return []
    records = []
    for item in value:
        if isinstance(item, dict):
            record = {field: _string(item.get(field)) for field in fields}
            record.update({field: _string_list(item.get(field)) for field in list_fields})
            records.append(record)
    return records


def _normalise_resume(data):
    if not isinstance(data, dict):
        raise ResumeParserError("The AI response was not a JSON object. Please try again.")
    result = _empty_resume()
    personal = data.get("personal_info", {})
    if isinstance(personal, dict):
        result["personal_info"] = {key: _string(personal.get(key)) for key in result["personal_info"]}
    result["summary"] = _string(data.get("summary"))
    result["skills"] = _string_list(data.get("skills"))
    result["experience"] = _records(data.get("experience"), ("company", "role", "location", "start_date", "end_date"), ("description",))
    result["education"] = _records(data.get("education"), ("degree", "institution", "location", "start_date", "end_date"))
    result["projects"] = _records(data.get("projects"), ("name",), ("description", "technologies"))
    result["certifications"] = _records(data.get("certifications"), ("name", "issuer", "date"))
    return result


def _decode_json_object(text):
    """Return the first complete JSON object in a model response."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ResumeParserError("The AI returned invalid or incomplete JSON. Please try parsing the resume again.")


def parse_json_response(response):
    """Parse model JSON, including JSON surrounded by prose or Markdown fences."""
    if not isinstance(response, str) or not response.strip():
        raise ResumeParserError("The AI returned an empty response. Please try again.")
    candidate = response.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        return _normalise_resume(_decode_json_object(candidate))
    except ResumeParserError:
        raise


def parse_resume(text):
    """Send clean resume text to Groq and return schema-normalised resume JSON."""
    if not isinstance(text, str) or not text.strip():
        raise ResumeParserError("There is no readable resume text to parse.")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ResumeParserError("GROQ_API_KEY is missing. Add it to your .env file and restart Streamlit.")
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": RESUME_PARSER_PROMPT.replace("{resume_text}", text)}],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0,
        )
        return parse_json_response(response.choices[0].message.content)
    except ResumeParserError:
        raise
    except Exception as exc:
        raise ResumeParserError("We couldn't parse the resume with Groq. Check your API key and try again.") from exc
