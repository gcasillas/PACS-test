# Lean demo workflow (Orthanc + Python)

This project keeps the integration intentionally lightweight:

- DICOM + SEG generation/push via Python scripts under `dicom/`
- HL7v2-to-FHIR conversion via file-based script under `hl7/`
- A reference mapping file under `fhir/`
- A single Docker service (`orthanc`) for DICOM test ingestion

## 1) Start Orthanc

```bash
docker compose up -d
```

## 2) Parse sample HL7 and emit FHIR Patient

```bash
python3 hl7/hl7_to_fhir.py
```

Outputs:

- `hl7/parsed_event.json`
- `fhir/Patient_MRN12345.json`

## 3) Ingest DICOM into Orthanc (optional)

```bash
dcmsend localhost 4242 0002.DCM -aet Dev_PACS -aec Dev_PACS
```

## 4) Generate SEG

```bash
python3 dicom/generate_seg.py
```

Output:

- `ai_mask.dcm`

## 5) Push DICOM + SEG

```bash
python3 dicom/cloud_push.py
```

You can still use root wrappers (`generate_seg.py`, `cloud_push.py`) for backward compatibility.
