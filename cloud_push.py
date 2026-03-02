import runpy
from pathlib import Path


if __name__ == "__main__":
    script_path = Path(__file__).resolve().parent / "dicom" / "cloud_push.py"
    runpy.run_path(str(script_path), run_name="__main__")