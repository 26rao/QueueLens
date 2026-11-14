import re
from typing import Dict, List, Optional, Tuple

DOCTOR_NAME_MAP = {
    "rao": "D01", "dr. rao": "D01", "dr rao": "D01",
    "sharma": "D02", "dr. sharma": "D02", "dr sharma": "D02",
    "shah": "D03", "dr. shah": "D03", "dr shah": "D03",
    "mehta": "D04", "dr. mehta": "D04", "dr mehta": "D04",
    "nair": "D05", "dr. nair": "D05", "dr nair": "D05",
}
KNOWN_SPECIALTIES = {"general", "cardiology", "orthopedics"}


def _match_doctor(text: str) -> Optional[str]:
    text_lower = text.lower()
    for name, did in DOCTOR_NAME_MAP.items():
        if name in text_lower:
            return did
    return None


def parse_deterministic(text: str) -> List[Dict]:
    actions = []
    text_lower = text.lower()

    unav_patterns = [
        r"dr\.?\s+(\w+)\s+(?:is\s+)?unavailable(?:\s+for\s+(\d+)\s+minutes?)?",
        r"(\w+)\s+is\s+unavailable(?:\s+for\s+(\d+)\s+minutes?)?",
    ]
    for pat in unav_patterns:
        for m in re.finditer(pat, text_lower):
            name = m.group(1)
            duration = int(m.group(2)) if m.lastindex >= 2 and m.group(2) else 60
            did = (
                DOCTOR_NAME_MAP.get(f"dr. {name}")
                or DOCTOR_NAME_MAP.get(f"dr {name}")
                or DOCTOR_NAME_MAP.get(name)
            )
            if did and not any(
                a["type"] == "doctor_unavailable" and a["doctor_id"] == did for a in actions
            ):
                actions.append({"type": "doctor_unavailable", "doctor_id": did, "duration_minutes": duration})

    avail_patterns = [
        r"dr\.?\s+(\w+)\s+(?:is\s+)?available(?:\s+again)?",
    ]
    for pat in avail_patterns:
        for m in re.finditer(pat, text_lower):
            name = m.group(1)
            did = (
                DOCTOR_NAME_MAP.get(f"dr. {name}")
                or DOCTOR_NAME_MAP.get(f"dr {name}")
                or DOCTOR_NAME_MAP.get(name)
            )
            if did:
                # Don't add available if already unavailable in same parse
                if not any(a["type"] == "doctor_unavailable" and a["doctor_id"] == did for a in actions):
                    if not any(a["type"] == "doctor_available" and a["doctor_id"] == did for a in actions):
                        actions.append({"type": "doctor_available", "doctor_id": did})

    em_patterns = [
        r"add\s+(\d+)\s+emergency\s+patients?",
        r"(\d+)\s+emergency\s+(?:patients?|arrivals?)",
    ]
    for pat in em_patterns:
        for m in re.finditer(pat, text_lower):
            count = min(int(m.group(1)), 10)
            if not any(a["type"] == "add_emergency" for a in actions):
                actions.append({
                    "type": "add_emergency",
                    "count": count,
                    "duration_minutes": 20,
                    "required_specialty": "general",
                })

    cancel_patterns = [
        r"cancel\s+appointment\s+([A-Za-z0-9\-]+)",
    ]
    for pat in cancel_patterns:
        for m in re.finditer(pat, text_lower):
            appt_id = m.group(1).upper()
            actions.append({"type": "cancel_appointment", "appointment_id": appt_id})

    return actions


async def parse_with_llm(text: str, settings) -> List[Dict]:
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )
        system_prompt = (
            'You parse hospital disruption commands into structured JSON.\n'
            'Return ONLY valid JSON: {"actions": [...]}\n'
            'Each action has a "type" field and optional fields:\n'
            '- doctor_unavailable: {type, doctor_id (D01-D05), duration_minutes}\n'
            '- doctor_available: {type, doctor_id}\n'
            '- add_emergency: {type, count (1-10), duration_minutes (default 20), required_specialty}\n'
            '- cancel_appointment: {type, appointment_id}\n'
            'Return {"actions": []} if unclear.'
        )
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=500,
        )
        import json
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed.get("actions", [])
    except Exception:
        return parse_deterministic(text)


async def parse_disruption(text: str, settings) -> Tuple[List[Dict], str]:
    if settings.LLM_ENABLED and settings.LLM_API_KEY:
        actions = await parse_with_llm(text, settings)
        return actions, "llm"
    actions = parse_deterministic(text)
    return actions, "deterministic"
