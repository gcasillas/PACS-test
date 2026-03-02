import argparse
import os
from typing import Any

from pydicom import dcmread
from pydicom.dataset import Dataset


def _iter_datasets(value: Any):
    if isinstance(value, Dataset):
        yield value
        for element in value:
            if element.VR == "SQ":
                for item in element.value:
                    if isinstance(item, Dataset):
                        yield from _iter_datasets(item)


def _segment_references_source(seg_ds: Dataset, source_ds: Dataset) -> bool:
    source_series_uid = str(source_ds.SeriesInstanceUID)
    source_sop_uid = str(source_ds.SOPInstanceUID)

    for ds in _iter_datasets(seg_ds):
        series_uid = getattr(ds, "SeriesInstanceUID", None)
        if series_uid and str(series_uid) != source_series_uid:
            continue

        for element in ds:
            if element.keyword != "ReferencedSOPInstanceUID":
                continue
            if str(element.value) == source_sop_uid:
                return True

    return False


def validate(source_path: str, seg_path: str) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if not os.path.isfile(source_path):
        errors.append(f"Missing source DICOM: {source_path}")
    if not os.path.isfile(seg_path):
        errors.append(f"Missing SEG DICOM: {seg_path}")

    if errors:
        return False, errors

    source_ds = dcmread(source_path)
    seg_ds = dcmread(seg_path)

    if getattr(seg_ds, "Modality", "") != "SEG":
        errors.append("SEG file Modality is not SEG.")

    if str(getattr(seg_ds, "StudyInstanceUID", "")) != str(getattr(source_ds, "StudyInstanceUID", "")):
        errors.append("StudyInstanceUID mismatch between source and SEG.")

    source_for_uid = getattr(source_ds, "FrameOfReferenceUID", None)
    seg_for_uid = getattr(seg_ds, "FrameOfReferenceUID", None)
    if source_for_uid and seg_for_uid and str(source_for_uid) != str(seg_for_uid):
        errors.append("FrameOfReferenceUID mismatch between source and SEG.")

    if not _segment_references_source(seg_ds, source_ds):
        errors.append("SEG does not reference the source SOP Instance UID.")

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate source + SEG pair before push.")
    parser.add_argument("--source", default=os.getenv("INPUT_DICOM", "0002.DCM"), help="Source DICOM path")
    parser.add_argument("--seg", default=os.getenv("SEG_OUTPUT_DICOM", "ai_mask.dcm"), help="SEG DICOM path")
    args = parser.parse_args()

    ok, errors = validate(args.source, args.seg)
    if ok:
        print("✅ Validation passed: SEG references source and core UIDs are aligned.")
        return

    print("❌ Validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()