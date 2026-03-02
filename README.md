# PACS-test
Orthanc for building (AI + DICOM + FHIR mapping)

## Extended pipeline: ingest → AI → SEG → push

This repo now supports generating a DICOM SEG (`ai_mask.dcm`) as a stage in the same pipeline and then pushing both source + SEG together.

Default flow:

1. Input image: `0002.DCM`
2. SEG stage: `generate_seg.py` creates `ai_mask.dcm`
3. Validation stage: `validate_pipeline.py` checks source/SEG linkage
4. Push stage: `cloud_push.py` sends both files to the destination AE

`generate_seg.py` creates SEG objects from the source image metadata so references are preserved for viewer overlay behavior.

## Shared configuration

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Key settings:

- `INPUT_DICOM`, `SEG_OUTPUT_DICOM`
- `LEGACY_XA_MODE` (set `true` only for legacy multiframe XA without spatial tags)
- `SOURCE_AET`, `DEST_AET`, `DEST_IP`, `DEST_PORT`
- `ORTHANC_URL`, `CLOUD_GATEWAY_URL`, `CLOUD_GATEWAY_API_KEY`
- `INPUT_FILES` (defaults to `0002.DCM,ai_mask.dcm`)

To run `generate_seg.py` directly with legacy compatibility mode:

```bash
python generate_seg.py --legacy-xa-mode
```

## Run `cloud_push.py` reliably

Use a virtual environment so decoder dependencies survive container/package differences.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python cloud_push.py
```

`cloud_push.py` supports three input modes:

1. `INPUT_FILES` env var (comma-separated file list)
2. `ZIP_FILE` extraction (legacy path)
3. Auto-discover local `*.dcm` files

If you recreate the container, rerun the commands above before running `cloud_push.py`.

Or run everything in one command:

```bash
./run_cloud_push.sh
```

The script installs dependencies only when `requirements.txt` changes.

## Run full pipeline locally

```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

Run validation only:

```bash
python validate_pipeline.py --source 0002.DCM --seg ai_mask.dcm
```

## Run as additional service(s) with Docker Compose

```bash
cp .env.example .env
docker compose up --build seg-generator cloud-push
```

- `seg-generator` runs `generate_seg.py`
- `cloud-push` runs validation and then pushes both source + SEG
