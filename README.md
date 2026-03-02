# PACS-test

Lean demo stack for DICOM + SEG + HL7v2 → FHIR conversion.

## Repository layout

```text
PACS-test/
├── docker-compose.yml          # Orthanc only
├── dicom/
│   ├── generate_seg.py         # AI-like mask to DICOM SEG
│   └── cloud_push.py           # push local DICOM files via C-STORE
├── hl7/
│   ├── sample_adt.txt          # mock ADT^A01 message
│   └── hl7_to_fhir.py          # parse HL7 and emit FHIR Patient JSON
├── fhir/
│   └── mappings.json           # mapping reference
├── docs/
│   └── README.md               # full walkthrough
└── .env.example                # minimal config template
```

Root scripts `generate_seg.py` and `cloud_push.py` are wrappers for backward compatibility.

## Quick start

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
docker compose up -d
```

## Demo workflow

```bash
# 1) HL7 v2 to FHIR Patient
python3 hl7/hl7_to_fhir.py

# 2) Generate SEG from source DICOM
python3 dicom/generate_seg.py

# 3) Validate source/SEG link (optional)
python3 validate_pipeline.py --source 0002.DCM --seg ai_mask.dcm

# 4) Push source + SEG
python3 dicom/cloud_push.py
```

See `docs/README.md` for the complete walkthrough.
