import os
import shutil
import zipfile
from pynetdicom import AE, ALL_TRANSFER_SYNTAXES  # <--- Added ALL_TRANSFER_SYNTAXES here
from pydicom import dcmread
from pydicom.dataset import FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

# 1. Configuration
ZIP_FILE = os.getenv("ZIP_FILE", "migrated_study.zip")
EXTRACT_DIR = os.getenv("EXTRACT_DIR", "temp_dicom")
INPUT_FILES_ENV = os.getenv("INPUT_FILES", "")
DEST_IP = os.getenv("DEST_IP", "localhost")
DEST_PORT = int(os.getenv("DEST_PORT", "4242"))
DEST_AET = os.getenv("DEST_AET", "CLOUD_GATEWAY")
SOURCE_AET = os.getenv("SOURCE_AET", "GABE_MIGRATOR")


def discover_dicom_sources() -> list[tuple[str, str]]:
    if INPUT_FILES_ENV.strip():
        discovered_files = []
        for item in INPUT_FILES_ENV.split(","):
            file_path = item.strip()
            if not file_path:
                continue
            if os.path.isfile(file_path):
                discovered_files.append((os.path.basename(file_path), file_path))
            else:
                print(f"⚠️ File listed in INPUT_FILES not found: {file_path}")
        return discovered_files

    if os.path.exists(ZIP_FILE):
        if os.path.isdir(EXTRACT_DIR):
            shutil.rmtree(EXTRACT_DIR)
        print(f"📦 Unpacking {ZIP_FILE}...")
        with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)

        discovered_files = []
        for root, _, files in os.walk(EXTRACT_DIR):
            for file_name in files:
                if file_name.lower().endswith(".dcm") or "." not in file_name:
                    file_path = os.path.join(root, file_name)
                    discovered_files.append((file_name, file_path))
        return discovered_files

    discovered_files = []
    for file_name in os.listdir("."):
        if file_name.lower().endswith(".dcm") and os.path.isfile(file_name):
            discovered_files.append((file_name, file_name))
    return discovered_files


# 2. Resolve input DICOM files
input_candidates = discover_dicom_sources()
if not input_candidates:
    raise SystemExit("❌ No DICOM input files found. Set INPUT_FILES or provide ZIP_FILE/.dcm files.")

# 3. Initialize the DICOM Sender (SCU)
ae = AE(ae_title=SOURCE_AET)

# 4. Loop and Push
print(f"🚀 Pushing studies to {DEST_AET} at {DEST_IP}:{DEST_PORT}...")

dicom_files = []
requested_contexts = set()

for file_name, file_path in input_candidates:
    try:
        ds = dcmread(file_path)
    except Exception as exc:
        print(f"⚠️ Skipping unreadable file {file_name}: {exc}")
        continue

    sop_class_uid = str(ds.SOPClassUID)
    if sop_class_uid not in requested_contexts:
        ae.add_requested_context(ds.SOPClassUID, ALL_TRANSFER_SYNTAXES)
        requested_contexts.add(sop_class_uid)

    dicom_files.append((file_name, ds))

assoc = ae.associate(DEST_IP, DEST_PORT, ae_title=DEST_AET)

if not assoc.is_established:
    print(f"❌ Failed to connect to {DEST_AET}")
else:
    for file, ds in dicom_files:
        try:
            status = assoc.send_c_store(ds)
            print(f"✅ Sent {file}: Status {status}")
        except ValueError as exc:
            if "No presentation context" not in str(exc):
                print(f"❌ Failed {file}: {exc}")
                continue

            print(f"⚠️ Retrying {file} after decompression fallback...")
            try:
                fallback_ds = ds.copy()
                fallback_ds.decompress()

                if not hasattr(fallback_ds, "file_meta") or fallback_ds.file_meta is None:
                    fallback_ds.file_meta = FileMetaDataset()

                fallback_ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                fallback_ds.is_little_endian = True
                fallback_ds.is_implicit_VR = False

                status = assoc.send_c_store(fallback_ds)
                print(f"✅ Sent {file} (fallback): Status {status}")
            except Exception as fallback_exc:
                print(f"❌ Failed {file}: compressed syntax not accepted and fallback failed ({fallback_exc})")

    assoc.release()

print("🏁 Migration simulation complete!")