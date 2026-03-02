import json
from datetime import datetime
from pathlib import Path

import hl7

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ADT_PATH = ROOT / "hl7" / "sample_adt.txt"
PARSED_EVENT_PATH = ROOT / "hl7" / "parsed_event.json"
FHIR_DIR = ROOT / "fhir"


def _safe_field(segment, field_index: int) -> str:
    if len(segment) <= field_index:
        return ""
    return str(segment[field_index]).strip()


def _safe_component(field_value: str, component_index: int) -> str:
    if not field_value:
        return ""
    components = field_value.split("^")
    if len(components) <= component_index:
        return ""
    return components[component_index].strip()


def _hl7_name_to_display(family_name: str, given_name: str) -> str:
    return " ".join(part for part in [given_name, family_name] if part).strip()


def _to_fhir_birth_date(hl7_date: str) -> str:
    if len(hl7_date) == 8 and hl7_date.isdigit():
        return f"{hl7_date[0:4]}-{hl7_date[4:6]}-{hl7_date[6:8]}"
    return ""


def parse_adt_to_event(message_str: str) -> dict:
    normalized_message = message_str.replace("\r\n", "\n").replace("\r", "\n")
    normalized_message = "\r".join(line for line in normalized_message.split("\n") if line.strip())
    msg = hl7.parse(normalized_message)
    pid = msg.segment("PID")
    pv1 = msg.segment("PV1")

    patient_id_field = _safe_field(pid, 3)
    patient_name_field = _safe_field(pid, 5)
    admission_location_field = _safe_field(pv1, 3)

    mrn = _safe_component(patient_id_field, 0)
    family_name = _safe_component(patient_name_field, 0)
    given_name = _safe_component(patient_name_field, 1)

    event = {
        "mrn": mrn,
        "family_name": family_name,
        "given_name": given_name,
        "name": _hl7_name_to_display(family_name, given_name),
        "dob": _safe_field(pid, 7),
        "gender": _safe_field(pid, 8),
        "patient_class": _safe_field(pv1, 2),
        "admission_location": _safe_component(admission_location_field, 0),
        "timestamp": datetime.now().isoformat(),
    }
    return event


def event_to_fhir_patient(event: dict) -> dict:
    gender_map = {"M": "male", "F": "female", "O": "other", "U": "unknown"}

    return {
        "resourceType": "Patient",
        "id": event["mrn"],
        "identifier": [
            {
                "system": "http://hospital.example.com/mrn",
                "value": event["mrn"],
            }
        ],
        "name": [
            {
                "text": event["name"],
                "family": event["family_name"],
                "given": [event["given_name"]] if event["given_name"] else [],
            }
        ],
        "gender": gender_map.get(event.get("gender", "").upper(), "unknown"),
        "birthDate": _to_fhir_birth_date(event.get("dob", "")),
    }


def main() -> None:
    message = SAMPLE_ADT_PATH.read_text(encoding="utf-8")
    event = parse_adt_to_event(message)

    PARSED_EVENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PARSED_EVENT_PATH.write_text(json.dumps(event, indent=2), encoding="utf-8")

    fhir_patient = event_to_fhir_patient(event)
    FHIR_DIR.mkdir(parents=True, exist_ok=True)
    patient_path = FHIR_DIR / f"Patient_{event['mrn']}.json"
    patient_path.write_text(json.dumps(fhir_patient, indent=2), encoding="utf-8")

    print(f"HL7 event parsed: {PARSED_EVENT_PATH}")
    print(f"FHIR Patient generated: {patient_path}")


if __name__ == "__main__":
    main()
