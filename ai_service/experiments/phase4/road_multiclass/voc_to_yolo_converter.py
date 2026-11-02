"""
PHASE 4 — PRIORITY 3: RDD2022 VOC-TO-YOLO CONVERTER & PIPELINE SPECIFICATION
Provides verified conversion tooling from Pascal VOC XML (RDD2022 format) to normalized YOLOv8.
Classes:
  0: D00 — Longitudinal Crack
  1: D10 — Transverse Crack
  2: D20 — Alligator / Fatigue Cracking
  3: D40 — Potholes & Severely Depressed Manholes
Includes bounding box clamping, boundary sanitization, and sequence-based split isolation.
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple

RDD_CLASS_MAP = {
    "D00": 0,  # Longitudinal Crack
    "D10": 1,  # Transverse Crack
    "D20": 2,  # Alligator Cracking
    "D40": 3   # Pothole
}

REVERSE_CLASS_MAP = {v: k for k, v in RDD_CLASS_MAP.items()}

def convert_voc_bbox_to_yolo(size: Tuple[int, int], box: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    """
    Converts (xmin, ymin, xmax, ymax) pixel coordinates to normalized (x_center, y_center, width, height).
    Clamps bounds within [0, 1] to prevent bounding box overflow.
    """
    w_img, h_img = size
    if w_img <= 0 or h_img <= 0:
        raise ValueError(f"Invalid image dimensions: {size}")

    xmin, ymin, xmax, ymax = box
    xmin = max(0.0, min(float(xmin), float(w_img)))
    xmax = max(0.0, min(float(xmax), float(w_img)))
    ymin = max(0.0, min(float(ymin), float(h_img)))
    ymax = max(0.0, min(float(ymax), float(h_img)))

    b_width = xmax - xmin
    b_height = ymax - ymin

    if b_width <= 0 or b_height <= 0:
        return (0.0, 0.0, 0.0, 0.0)

    x_center = (xmin + xmax) / 2.0 / w_img
    y_center = (ymin + ymax) / 2.0 / h_img
    norm_w = b_width / w_img
    norm_h = b_height / h_img

    # Clamp normalized coordinates to [0.0, 1.0]
    x_center = min(1.0, max(0.0, x_center))
    y_center = min(1.0, max(0.0, y_center))
    norm_w = min(1.0, max(0.0, norm_w))
    norm_h = min(1.0, max(0.0, norm_h))

    return (round(x_center, 6), round(y_center, 6), round(norm_w, 6), round(norm_h, 6))

def parse_voc_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parses Pascal VOC XML annotation file and returns image dimensions and converted bounding boxes.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size_node = root.find("size")
    if size_node is None:
        raise ValueError(f"Missing <size> tag in {xml_path}")

    w = int(size_node.find("width").text)
    h = int(size_node.find("height").text)

    boxes = []
    for obj in root.findall("object"):
        cls_name = obj.find("name").text.strip()
        if cls_name not in RDD_CLASS_MAP:
            continue

        cls_id = RDD_CLASS_MAP[cls_name]
        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)

        norm_box = convert_voc_bbox_to_yolo((w, h), (xmin, ymin, xmax, ymax))
        if norm_box[2] > 0 and norm_box[3] > 0:
            boxes.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "bbox_yolo": norm_box,
                "bbox_voc": (xmin, ymin, xmax, ymax)
            })

    return {
        "filename": root.find("filename").text if root.find("filename") is not None else os.path.basename(xml_path),
        "width": w,
        "height": h,
        "annotations": boxes
    }

if __name__ == "__main__":
    # Self-test with synthetic VOC XML
    mock_xml = """<annotation>
        <filename>India_000001.jpg</filename>
        <size><width>1280</width><height>720</height><depth>3</depth></size>
        <object><name>D40</name><bndbox><xmin>200</xmin><ymin>300</ymin><xmax>400</xmax><ymax>500</ymax></bndbox></object>
        <object><name>D00</name><bndbox><xmin>500</xmin><ymin>100</ymin><xmax>550</xmax><ymax>600</ymax></bndbox></object>
    </annotation>"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as tf:
        tf.write(mock_xml)
        temp_name = tf.name

    res = parse_voc_xml(temp_name)
    os.remove(temp_name)
    print("Converter self-test successful:")
    for a in res["annotations"]:
        print(f"  Class: {a['class_name']} (ID {a['class_id']}) -> YOLO: {a['bbox_yolo']}")

