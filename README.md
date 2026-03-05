# PACS-test

Lean demo stack for EMR + PACS + DICOM/SEG + HL7v2 → FHIR conversion.

## Current stack

- PACS: Orthanc (`4242` DICOM, `8042` web)
- EMR: OpenEMR (`8080` web)
- EMR DB: MariaDB (internal only)
- Python pipeline scripts for HL7→FHIR and DICOM SEG workflow

## Repository layout

```text
PACS-test/
├── docker-compose.yml          # Orthanc + OpenEMR + MariaDB
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
└── .env.example                # optional pipeline config template
```

Root scripts `generate_seg.py` and `cloud_push.py` are wrappers for backward compatibility.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
docker compose up -d
```

One-command demo startup (recommended):

```bash
./run_demo.sh
```

The script starts compose, waits for ports `8042` and `8080`, and prints login URLs/credentials.

Service UIs:

- Orthanc: http://localhost:8042
- OpenEMR: http://localhost:8080

Default demo credentials:

- Orthanc: `orthanc_user` / `orthanc_secure_pass`
- OpenEMR admin: `admin` / `AdminPass123!`

## Known-good startup (Codespaces)

Use this sequence to avoid repeated long rebuilds:

1. Rebuild once after compose/devcontainer changes.
2. Wait 2-4 minutes on first boot for OpenEMR initialization.
3. Open URLs in this order:
	- `http://127.0.0.1:8042`
	- `http://127.0.0.1:8080/`
	- `http://127.0.0.1:8080/interface/login/login.php?site=default`

For normal daily use (no config changes), prefer container restart over full rebuild:

```bash
docker compose restart
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
