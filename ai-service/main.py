import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel, Field


# ============================================================
# Configuration
# ============================================================

load_dotenv()

app = FastAPI(
    title="Equipment Maintenance AI Service"
)

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

KB = Path(__file__).parent / "knowledge_base"


# ============================================================
# Request Model
# ============================================================

class AnalyzeRequest(BaseModel):
    equipment: Dict[str, Any]
    issue: Dict[str, Any]
    thresholdChecks: List[Dict[str, Any]] = Field(
        default_factory=list
    )
    conflicts: List[Dict[str, Any]] = Field(
        default_factory=list
    )


# ============================================================
# Knowledge Base Retrieval
# ============================================================

def retrieve_evidence(
    payload: AnalyzeRequest
) -> List[Dict[str, Any]]:

    manual_path = KB / "sample_manual.txt"

    if not manual_path.exists():
        print("WARNING: sample_manual.txt was not found.")
        return []

    text = manual_path.read_text(
        encoding="utf-8"
    )

    equipment = payload.equipment
    issue = payload.issue

    query = " ".join(
        [
            str(equipment.get("type", "")),
            str(equipment.get("identifier", "")),
            str(issue.get("description", "")),
            str(issue.get("operatingEvents", "")),
        ]
    ).lower()

    sections = re.split(
        r"\n(?=Section:)",
        text
    )

    keywords = [
        "temperature",
        "vibration",
        "bearing",
        "inspection",
        "maintenance",
        "alignment",
        "imbalance",
        "motor",
        "overheating",
    ]

    results = []

    query_words = set(
        re.findall(
            r"[a-zA-Z0-9_-]+",
            query
        )
    )

    for section in sections:

        section = section.strip()

        if not section:
            continue

        section_lower = section.lower()

        score = 0

        # Match query words
        for word in query_words:

            if len(word) >= 4 and word in section_lower:
                score += 1

        # Match important maintenance keywords
        for keyword in keywords:

            if (
                keyword in query
                and keyword in section_lower
            ):
                score += 3

        if score > 0:

            first_line = section.splitlines()[0]

            results.append(
                {
                    "source": "sample_manual.txt",
                    "section": first_line
                    .replace("Section:", "")
                    .strip(),
                    "text": section,
                    "score": score,
                }
            )

    results.sort(
        key=lambda item: item.get(
            "score",
            0
        ),
        reverse=True
    )

    cleaned_results = []

    for item in results[:5]:

        cleaned_results.append(
            {
                "source": item["source"],
                "section": item["section"],
                "text": item["text"],
            }
        )

    return cleaned_results


# ============================================================
# Deterministic Priority
# ============================================================

def calculate_priority(
    payload: AnalyzeRequest
) -> str:

    for check in payload.thresholdChecks:

        if check.get("triggered") is True:
            return "HIGH"

    return "MEDIUM"


# ============================================================
# Deterministic Observations
# ============================================================

def build_observations(
    payload: AnalyzeRequest
) -> List[str]:

    observations = []

    issue = payload.issue

    # --------------------------------------------------------
    # Technician-reported issue
    # --------------------------------------------------------

    description = issue.get("description")

    if description:

        observations.append(
            f"Technician reported: {description}"
        )

    # --------------------------------------------------------
    # Operating events
    # --------------------------------------------------------

    operating_events = issue.get(
        "operatingEvents",
        []
    )

    if isinstance(
        operating_events,
        list
    ):

        for event in operating_events:

            if isinstance(
                event,
                dict
            ):

                event_text = (
                    event.get("description")
                    or event.get("event")
                    or event.get("name")
                )

                if event_text:

                    observations.append(
                        f"Recent operating event: {event_text}"
                    )

            elif event:

                observations.append(
                    f"Recent operating event: {event}"
                )

    elif operating_events:

        observations.append(
            f"Recent operating events: {operating_events}"
        )

    # --------------------------------------------------------
    # Sensor readings
    # --------------------------------------------------------

    sensor_readings = issue.get(
        "sensorReadings",
        []
    )

    if isinstance(
        sensor_readings,
        list
    ):

        for reading in sensor_readings:

            if not isinstance(
                reading,
                dict
            ):
                continue

            name = (
                reading.get("name")
                or reading.get("sensor")
                or reading.get("type")
            )

            value = reading.get(
                "value"
            )

            unit = (
                reading.get("unit")
                or ""
            )

            if (
                name
                and value is not None
            ):

                observations.append(
                    f"Reported {name}: {value}{unit}."
                )

    # --------------------------------------------------------
    # Deterministic threshold results
    # --------------------------------------------------------

    for check in payload.thresholdChecks:

        name = check.get(
            "name"
            or "code"
        )

        message = check.get(
            "message"
        )

        triggered = check.get(
            "triggered"
        )

        if message:

            status = (
                "TRIGGERED"
                if triggered
                else "NORMAL"
            )

            observations.append(
                f"{name}: {message} ({status})"
            )

    # --------------------------------------------------------
    # If nothing was supplied
    # --------------------------------------------------------

    if not observations:

        observations.append(
            "No direct technician observations were provided."
        )

    return observations


# ============================================================
# Fallback Analysis
# ============================================================

def fallback_result(
    payload: AnalyzeRequest,
    evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:

    priority = calculate_priority(
        payload
    )

    observations = build_observations(
        payload
    )

    return {
        "summary": (
            "The equipment issue requires "
            "technician review. The AI service "
            "was temporarily unavailable, so "
            "this result is based on deterministic "
            "threshold checks and available "
            "maintenance evidence."
        ),

        "observations": observations,

        "possible_causes": [
            {
                "cause": (
                    "Mechanical or thermal "
                    "operating condition"
                ),
                "reason": (
                    "The reported symptoms may "
                    "indicate a mechanical or "
                    "thermal condition requiring "
                    "inspection."
                ),
                "confidence": "medium"
            }
        ],

        "questions_for_technician": [
            "When did the reported abnormal condition first begin?",
            "Does the condition become worse when the equipment is under load?",
            "Has the equipment or the affected component been inspected or serviced recently?"
        ],

        "inspection_steps": [
            "Inspect the equipment for visible damage or abnormal conditions.",
            "Check temperature and vibration measurements.",
            "Inspect bearings and alignment where applicable.",
            "Review recent operating events and maintenance history."
        ],

        "priority": priority,

        "work_order_draft": {
            "title": (
                "Equipment condition inspection"
            ),
            "description": (
                "Inspect the reported equipment "
                "condition, verify measurements, "
                "identify the possible cause, "
                "and document confirmed findings."
            ),
            "recommended_priority": priority
        },

        "confirmed_findings": [],

        "evidence": evidence,

        "warnings": [
            (
                "Gemini was temporarily unavailable. "
                "This is a fallback analysis."
            ),
            (
                "Possible causes are hypotheses "
                "and are not confirmed findings."
            ),
            (
                "Technician review is required "
                "before maintenance action."
            )
        ]
    }


# ============================================================
# Gemini Analysis
# ============================================================

def analyze_with_gemini(
    payload: AnalyzeRequest,
    evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to ai-service/.env."
        )

    client = genai.Client(
        api_key=api_key
    )

    priority = calculate_priority(
        payload
    )

    context = {
        "equipment": payload.equipment,
        "issue": payload.issue,
        "threshold_checks": payload.thresholdChecks,
        "conflicts": payload.conflicts,
        "retrieved_manual_evidence": evidence
    }

    # --------------------------------------------------------
    # System Instructions
    # --------------------------------------------------------

    system_prompt = """
You are an equipment maintenance triage assistant.

Your job is to analyze equipment maintenance issues using:

1. Technician-provided observations.
2. Deterministic threshold checks.
3. Retrieved maintenance-manual evidence.

IMPORTANT RULES:

- Do NOT claim that a possible cause is confirmed.
- Possible causes must remain hypotheses.
- confirmed_findings MUST ALWAYS be an empty array.
- Only a technician can confirm a physical finding.
- Deterministic threshold checks are authoritative.
- If a threshold is triggered, do not downgrade its priority.
- Do not invent sensor readings.
- Do not invent maintenance history.
- Do not invent manual sections.
- Clearly mention missing or conflicting information.
- Recommend inspection steps rather than claiming a repair has been performed.
- The work order is only a draft.
- A technician must review, edit, approve, or reject the work order.
- Never recommend automatic equipment control.
- Never claim that maintenance has automatically been approved.

OBSERVATION RULES:

- observations must contain only information actually supplied in the case.
- Include technician-reported symptoms.
- Include provided sensor readings.
- Include relevant operating events.
- Include deterministic threshold results when useful.
- Do NOT turn possible causes into observations.
- Do NOT invent observations.
- Do NOT use observations to claim that a fault has been confirmed.

FOLLOW-UP QUESTION RULES:

- Always provide 2 to 3 targeted questions for the technician.
- Questions must be specific to the equipment issue.
- Questions should address missing information, uncertainty, operating conditions, recent maintenance, or symptoms that could help distinguish between possible causes.
- Do not ask questions whose answers are already explicitly provided.
- Never return an empty questions_for_technician array.

Return valid JSON only.
"""

    # --------------------------------------------------------
    # User Prompt
    # --------------------------------------------------------

    user_prompt = f"""
Analyze this equipment maintenance case.

CASE DATA:

{json.dumps(
    context,
    indent=2,
    default=str
)}

Return exactly this JSON structure:

{{
  "summary": "Short summary of the reported problem",

  "observations": [
    "Observation based only on information actually reported"
  ],

  "possible_causes": [
    {{
      "cause": "Possible cause",
      "reason": "Why this is a possibility",
      "confidence": "low | medium | high"
    }}
  ],

  "questions_for_technician": [
    "Question 1",
    "Question 2",
    "Question 3"
  ],

  "inspection_steps": [
    "Inspection step 1"
  ],

  "priority": "LOW | MEDIUM | HIGH",

  "work_order_draft": {{
    "title": "Draft work order title",
    "description": "Draft maintenance task description",
    "recommended_priority": "LOW | MEDIUM | HIGH"
  }},

  "confirmed_findings": [],

  "evidence": [],

  "warnings": [
    "Warning or limitation"
  ]
}}

OBSERVATION REQUIREMENTS:

- Return observations based only on the supplied case data.
- Include reported symptoms.
- Include supplied sensor readings.
- Include relevant operating events.
- Do not invent observations.
- Do not describe possible causes as observations.
- Do not describe an unverified fault as a confirmed finding.

FOLLOW-UP QUESTION REQUIREMENTS:

- Return 2 to 3 questions.
- Questions must be specific to this case.
- Ask about information that is missing from the case.
- Ask about timing, operating conditions, recent maintenance, unusual symptoms, or other information that could help distinguish between possible causes.
- Do not simply repeat information already provided.
- Never return an empty questions_for_technician array.

EVIDENCE RULES:

- Use only the retrieved manual evidence supplied above.
- Do not invent citations.
- Do not create manual sections that were not supplied.
- The application will replace the evidence field with the actual retrieved evidence.

DETERMINISTIC PRIORITY:

The application calculated:

{priority}

If this value is HIGH, your returned priority MUST be HIGH.
"""

    # ========================================================
    # Gemini Request With Retry
    # ========================================================

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                f"Calling Gemini "
                f"(attempt {attempt}/{max_attempts})..."
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=(
                    system_prompt
                    + "\n\n"
                    + user_prompt
                ),
                config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json"
                }
            )

            print(
                "Gemini response received."
            )

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            # ------------------------------------------------
            # Parse JSON
            # ------------------------------------------------

            try:

                result = json.loads(
                    response.text
                )

            except json.JSONDecodeError as json_error:

                print(
                    "GEMINI JSON ERROR:",
                    repr(json_error)
                )

                print(
                    "GEMINI RAW RESPONSE:",
                    response.text
                )

                raise RuntimeError(
                    "Gemini returned invalid JSON."
                ) from json_error

            return result

        except Exception as exc:

            error_text = str(exc)

            print(
                f"GEMINI ATTEMPT {attempt} FAILED:"
            )

            print(
                repr(exc)
            )

            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if (
                temporary_error
                and attempt < max_attempts
            ):

                wait_time = 2 ** (
                    attempt - 1
                )

                print(
                    f"Temporary Gemini error. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

                continue

            print(
                "GEMINI ERROR:",
                repr(exc)
            )

            raise RuntimeError(
                f"Gemini API request failed: {exc}"
            ) from exc

    raise RuntimeError(
        "Gemini request failed after all retry attempts."
    )


# ============================================================
# Grounding / Safety Layer
# ============================================================

def ground_result(
    result: Dict[str, Any],
    payload: AnalyzeRequest,
    evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Never allow AI to claim confirmed findings
    # --------------------------------------------------------

    result["confirmed_findings"] = []

    # --------------------------------------------------------
    # Evidence comes from our retrieval system
    # --------------------------------------------------------

    result["evidence"] = evidence

    # --------------------------------------------------------
    # Deterministic observations
    # --------------------------------------------------------

    deterministic_observations = (
        build_observations(payload)
    )

    # Use the actual case data as the authoritative
    # observation source.
    result["observations"] = (
        deterministic_observations
    )

    # --------------------------------------------------------
    # Deterministic priority
    # --------------------------------------------------------

    deterministic_priority = (
        calculate_priority(payload)
    )

    if deterministic_priority == "HIGH":

        result["priority"] = "HIGH"

    elif result.get("priority") not in {
        "LOW",
        "MEDIUM",
        "HIGH"
    }:

        result["priority"] = (
            deterministic_priority
        )

    # --------------------------------------------------------
    # Ensure required arrays exist
    # --------------------------------------------------------

    if not isinstance(
        result.get("possible_causes"),
        list
    ):
        result["possible_causes"] = []

    if not isinstance(
        result.get("questions_for_technician"),
        list
    ):
        result[
            "questions_for_technician"
        ] = []

    if not isinstance(
        result.get("inspection_steps"),
        list
    ):
        result["inspection_steps"] = []

    if not isinstance(
        result.get("warnings"),
        list
    ):
        result["warnings"] = []

    # --------------------------------------------------------
    # ALWAYS provide follow-up questions
    # --------------------------------------------------------

    questions = result.get(
        "questions_for_technician",
        []
    )

    questions = [
        str(question).strip()
        for question in questions
        if str(question).strip()
    ]

    if not questions:

        questions = [
            "When did the reported abnormal condition first begin?",
            "Does the condition become worse when the equipment is under load?",
            "Has the equipment or the affected component been inspected or serviced recently?"
        ]

    result[
        "questions_for_technician"
    ] = questions[:3]

    # --------------------------------------------------------
    # Required safety warning
    # --------------------------------------------------------

    hypothesis_warning = (
        "Possible causes are hypotheses "
        "and are not confirmed findings."
    )

    if hypothesis_warning not in result[
        "warnings"
    ]:

        result["warnings"].append(
            hypothesis_warning
        )

    # --------------------------------------------------------
    # Human review requirement
    # --------------------------------------------------------

    review_warning = (
        "Technician review is required "
        "before maintenance action."
    )

    if review_warning not in result[
        "warnings"
    ]:

        result["warnings"].append(
            review_warning
        )

    # --------------------------------------------------------
    # Sensor conflicts
    # --------------------------------------------------------

    if payload.conflicts:

        conflict_warning = (
            "Conflicting or inconsistent "
            "sensor data was reported. "
            "Technician verification is required."
        )

        if conflict_warning not in result[
            "warnings"
        ]:

            result["warnings"].append(
                conflict_warning
            )

    # --------------------------------------------------------
    # Missing sensor data
    # --------------------------------------------------------

    sensor_readings = payload.issue.get(
        "sensorReadings"
    )

    if not sensor_readings:

        sensor_warning = (
            "No sensor readings were provided. "
            "Recommendations are based on the "
            "reported symptoms and available "
            "manual evidence."
        )

        if sensor_warning not in result[
            "warnings"
        ]:

            result["warnings"].append(
                sensor_warning
            )

    # --------------------------------------------------------
    # Ensure work order exists
    # --------------------------------------------------------

    if not isinstance(
        result.get("work_order_draft"),
        dict
    ):

        result["work_order_draft"] = {
            "title": (
                "Equipment condition inspection"
            ),
            "description": (
                "Inspect the reported equipment "
                "condition and document confirmed "
                "findings."
            ),
            "recommended_priority": (
                result["priority"]
            )
        }

    # Always synchronize work order priority
    result[
        "work_order_draft"
    ][
        "recommended_priority"
    ] = result["priority"]

    return result


# ============================================================
# Health Endpoint
# ============================================================

@app.get("/health")
def health():

    return {
        "ok": True,
        "service": "ai-service",
        "provider": "google-gemini",
        "model": MODEL
    }


# ============================================================
# Analyze Endpoint
# ============================================================

@app.post("/analyze")
def analyze(
    payload: AnalyzeRequest
):

    try:

        print(
            "Received maintenance analysis request."
        )

        # ----------------------------------------------------
        # 1. Retrieve manual evidence
        # ----------------------------------------------------

        evidence = retrieve_evidence(
            payload
        )

        print(
            f"Retrieved {len(evidence)} "
            f"manual evidence section(s)."
        )

        # ----------------------------------------------------
        # 2. Call Gemini
        # ----------------------------------------------------

        try:

            result = analyze_with_gemini(
                payload,
                evidence
            )

        except Exception as gemini_error:

            print(
                "Gemini unavailable after retries:"
            )

            print(
                repr(gemini_error)
            )

            # ------------------------------------------------
            # Fallback
            # ------------------------------------------------

            result = fallback_result(
                payload,
                evidence
            )

        # ----------------------------------------------------
        # 3. Apply grounding/safety rules
        # ----------------------------------------------------

        result = ground_result(
            result,
            payload,
            evidence
        )

        print(
            "Maintenance analysis completed."
        )

        return result

    except Exception as exc:

        print(
            "ANALYZE ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=503,
            detail=(
                f"LLM analysis failed: {exc}"
            )
        )


# ============================================================
# Local Development Entry Point
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8002,
        reload=True
    )