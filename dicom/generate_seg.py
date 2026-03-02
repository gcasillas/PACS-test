import argparse
import copy
import os

import numpy as np
from highdicom.content import AlgorithmIdentificationSequence
from highdicom.seg import (
    SegmentAlgorithmTypeValues,
    SegmentDescription,
    Segmentation,
    SegmentationTypeValues,
)
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.sr.codedict import codes
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


def build_binary_mask(source_ds, threshold_percentile: float) -> np.ndarray:
    if "PixelData" not in source_ds:
        raise ValueError("Input DICOM has no PixelData and cannot be converted to SEG.")

    pixel_array = source_ds.pixel_array
    if pixel_array.ndim == 2:
        pixel_array = pixel_array[np.newaxis, ...]

    pixel_float = pixel_array.astype(np.float32)
    cutoff = np.percentile(pixel_float, threshold_percentile)
    mask = (pixel_float >= cutoff).astype(np.uint8)
    return mask


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def prepare_source_for_seg(source_ds, legacy_xa_mode: bool):
    has_frame_of_reference_uid = bool(getattr(source_ds, "FrameOfReferenceUID", None))

    number_of_frames = int(getattr(source_ds, "NumberOfFrames", 1) or 1)
    has_spatial_tags = all(
        getattr(source_ds, keyword, None) is not None
        for keyword in ["ImagePositionPatient", "ImageOrientationPatient", "PixelSpacing"]
    )

    if legacy_xa_mode and number_of_frames > 1 and not has_spatial_tags:
        print("⚠️ Source is multiframe without spatial coordinates; using first frame for SEG compatibility...")
        pixel_array = source_ds.pixel_array
        first_frame = pixel_array[0]

        single_frame_source = copy.deepcopy(source_ds)
        single_frame_source.NumberOfFrames = 1

        if "PerFrameFunctionalGroupsSequence" in single_frame_source:
            single_frame_source.PerFrameFunctionalGroupsSequence = [
                single_frame_source.PerFrameFunctionalGroupsSequence[0]
            ]

        single_frame_source.Rows = first_frame.shape[0]
        single_frame_source.Columns = first_frame.shape[1]
        single_frame_source.PixelData = first_frame.tobytes()
        single_frame_source.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        single_frame_source.is_little_endian = True
        single_frame_source.is_implicit_VR = False

        if "SharedFunctionalGroupsSequence" not in single_frame_source:
            pixel_measures_item = Dataset()
            pixel_measures_item.PixelSpacing = [1.0, 1.0]
            pixel_measures_item.SliceThickness = 1.0

            shared_fg_item = Dataset()
            shared_fg_item.PixelMeasuresSequence = Sequence([pixel_measures_item])
            single_frame_source.SharedFunctionalGroupsSequence = Sequence([shared_fg_item])

        if "FrameOfReferenceUID" in single_frame_source and not has_frame_of_reference_uid:
            del single_frame_source.FrameOfReferenceUID

        return single_frame_source

    if not has_frame_of_reference_uid:
        source_ds.FrameOfReferenceUID = generate_uid()
        print("⚠️ Patching missing FrameOfReferenceUID for SEG alignment...")

    return source_ds


def create_seg(input_path: str, output_path: str, threshold_percentile: float, legacy_xa_mode: bool) -> None:
    source_ds = dcmread(input_path)
    source_ds = prepare_source_for_seg(source_ds, legacy_xa_mode=legacy_xa_mode)

    mask = build_binary_mask(source_ds, threshold_percentile)

    segment = SegmentDescription(
        segment_number=1,
        segment_label="AI Mask",
        segmented_property_category=codes.SCT.Tissue,
        segmented_property_type=codes.SCT.Lesion,
        algorithm_type=SegmentAlgorithmTypeValues.AUTOMATIC,
        algorithm_identification=AlgorithmIdentificationSequence(
            name="SimpleThreshold",
            family=codes.DCM.ArtificialIntelligence,
            version="1.0.0",
        ),
        tracking_uid=generate_uid(),
        tracking_id="AI_MASK_1",
    )

    seg = Segmentation(
        source_images=[source_ds],
        pixel_array=mask,
        segmentation_type=SegmentationTypeValues.BINARY,
        segment_descriptions=[segment],
        series_instance_uid=generate_uid(),
        sop_instance_uid=generate_uid(),
        series_number=300,
        instance_number=1,
        manufacturer="PACS-test",
        manufacturer_model_name="seg-generator",
        software_versions="1.0.0",
        device_serial_number="SEG-STAGE",
        omit_empty_frames=False,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    seg.save_as(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DICOM SEG from an input DICOM image.")
    parser.add_argument("--input", default=os.getenv("INPUT_DICOM", "0002.DCM"), help="Input DICOM path")
    parser.add_argument("--output", default=os.getenv("SEG_OUTPUT_DICOM", "ai_mask.dcm"), help="Output SEG path")
    parser.add_argument(
        "--threshold-percentile",
        type=float,
        default=float(os.getenv("SEG_THRESHOLD_PERCENTILE", "80")),
        help="Intensity percentile used to generate a demo binary mask",
    )
    parser.add_argument(
        "--legacy-xa-mode",
        action=argparse.BooleanOptionalAction,
        default=env_bool("LEGACY_XA_MODE", False),
        help="Enable compatibility mode for legacy multiframe XA without spatial coordinates",
    )
    args = parser.parse_args()

    create_seg(
        args.input,
        args.output,
        args.threshold_percentile,
        args.legacy_xa_mode,
    )
    print(f"✅ SEG generated: {args.output}")


if __name__ == "__main__":
    main()
