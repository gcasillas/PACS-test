import requests
import json

# 1. Configuration
ORTHANC_URL = "http://localhost:8042"
STUDY_UID = "1.3.12.2.1107.5.4.3.123456789012345.19950922.121803.6"

# 2. Find the Orthanc Internal ID
lookup = requests.post(f"{ORTHANC_URL}/tools/lookup", data=STUDY_UID).json()
if not lookup:
    print("Study not found!")
    exit()

orthanc_id = lookup[0]['ID']

# 3. Morph the tags
modification = {
    "Replace": {
        "Manufacturer": "Gabe-Cloud-Imaging-v1",
        "InstitutionName": "Jefferson Health Preview"
    },
    "Force": True
}

print(f"🔄 Morphing tags for study {STUDY_UID}...")
response = requests.post(f"{ORTHANC_URL}/studies/{orthanc_id}/modify", json=modification)

if response.status_code == 200:
    # Get the ID of the NEWLY created study (the morphed one)
    new_study_id = response.json()['ID']
    print("✅ Success! The study now has a Manufacturer and Institution name.")
    
    # 4. DOWNLOAD the new DCM.zip
    print("📦 Exporting cleaned study...")
    archive_resp = requests.get(f"{ORTHANC_URL}/studies/{new_study_id}/archive")
    with open("migrated_study.zip", "wb") as f:
        f.write(archive_resp.content)
    print("🚀 Done! 'migrated_study.zip' is now in your file explorer.")
else:
    print(f"❌ Failed to morph tags: {response.text}")