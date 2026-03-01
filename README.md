# PACS-test
Orthanc for building (AI + DICOM + FHIR mapping)

## Run `cloud_push.py` reliably

Use a virtual environment so decoder dependencies survive container/package differences.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python cloud_push.py
```

If you recreate the container, rerun the commands above before running `cloud_push.py`.

Or run everything in one command:

```bash
./run_cloud_push.sh
```

The script installs dependencies only when `requirements.txt` changes.
