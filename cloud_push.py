import os
import zipfile
import requests
from pynetdicom import AE, ALL_TRANSFER_SYNTAXES  # <--- Added ALL_TRANSFER_SYNTAXES here
from pydicom import dcmread
from pydicom.dataset import FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

# 1. Configuration
ZIP_FILE = "migrated_study.zip"
EXTRACT_DIR = "temp_dicom"
DEST_IP = "localhost"
DEST_PORT = 4242  # In a real move, this would be a Cloud Gateway port
DEST_AET = "CLOUD_GATEWAY"

# 2. Extract the files
print(f"📦 Unpacking {ZIP_FILE}...")
with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
    zip_ref.extractall(EXTRACT_DIR)

# 3. Initialize the DICOM Sender (SCU)
ae = AE(ae_title="GABE_MIGRATOR")

# 4. Loop and Push
print(f"🚀 Pushing studies to {DEST_AET}...")

dicom_files = []
requested_contexts = set()

for root, dirs, files in os.walk(EXTRACT_DIR):
    for file in files:
        if file.lower().endswith(".dcm") or "." not in file:
            file_path = os.path.join(root, file)
            try:
                ds = dcmread(file_path)
            except Exception as exc:
                print(f"⚠️ Skipping unreadable file {file}: {exc}")
                continue

            sop_class_uid = str(ds.SOPClassUID)
            if sop_class_uid not in requested_contexts:
                ae.add_requested_context(ds.SOPClassUID, ALL_TRANSFER_SYNTAXES)
                requested_contexts.add(sop_class_uid)

            dicom_files.append((file, ds))

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