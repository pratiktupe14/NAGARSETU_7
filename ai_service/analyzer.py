import io
import uuid
import hashlib
from typing import Dict, Any, Optional
from PIL import Image
from ai_service.graph.workflow import run_civic_vision_pipeline
from ai_service.model_manager import evaluate_civic_image_gate


def analyze_complaint_image(
    image_bytes: bytes,
    filename: str = "",
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes complaint image using the compiled LangGraph YOLOv8 agent system
    and authoritative 4-outcome Civic Image Decision Gate.
    Completely removes Gemini Vision. Uses 100% local computer-vision inference.
    Returns both the standard rich LangGraph agent result and backward-compatible fields.
    """
    analysis_id = str(uuid.uuid4())
    image_hash = hashlib.sha256(image_bytes).hexdigest()

    # Pre-parse PIL image for validation gate
    pil_img = None
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        pass

    result = run_civic_vision_pipeline(
        image_bytes=image_bytes,
        filename=filename,
        domain=domain
    )

    complaint = result.get("complaint")
    ai_status = result.get("aiStatus", "manual_review")
    has_valid_complaint = (ai_status in ("confirmed", "suggested") and complaint is not None)
    road_condition = result.get("road_condition")

    primary = result.get("primaryDetection")
    detections = result.get("detections") or []
    detected_features = [d.get("class") for d in detections if d.get("class")]

    # Run Civic Image Decision Gate
    gate = None
    if pil_img is not None:
        try:
            gate = evaluate_civic_image_gate(pil_img, domain=domain, detections=detections)
        except Exception as e:
            gate = None

    # CASE 4: NON-CIVIC SUBJECT -> Immediate Rejection
    if gate and gate["outcome"] == "INVALID_IMAGE":
        return {
            "success": True,
            "decision_outcome": "INVALID_IMAGE",
            "decision_message": "This is not a civic issue. Please upload a valid civic image.",
            "outcome": "INVALID_IMAGE",
            "message": "This is not a civic issue. Please upload a valid civic image.",
            "allow_manual": False,
            "allowManualEntry": False,
            "accepted_as_evidence": False,
            "acceptedAsEvidence": False,
            "aiStatus": "invalid_image",
            "ai_status": "invalid_image",
            "detected": False,
            "is_civic_issue": False,
            "category": None,
            "issue_type": None,
            "title": None,
            "description": "This is not a civic issue. Please upload a valid civic image.",
            "severity": "None",
            "priority": "None",
            "department": None,
            "department_code": None,
            "departmentCode": None,
            "department_id": None,
            "recommended_department": None,
            "confidence": 0.0,
            "civic_validation": gate.get("civic_validation"),
            "surface_metrics": gate.get("surface_metrics"),
            "road_condition": "non_road",
            "primaryDetection": None,
            "detections": [],
            "analysis": {"visualImpactScore": 0.0, "detectionCount": 0, "hasMultipleDetections": False, "allDetections": []},
            "complaint": None,
            "explanation": "This is not a civic issue. Please upload a valid civic image.",
            "explanation_details": {"reason": "This is not a civic issue. Please upload a valid civic image."},
            "reviewRequired": False,
            "review_required": False,
            "analysis_id": analysis_id,
            "image_hash": image_hash,
            "model": "civic_validator.pt",
            "detected_features": [],
            "needs_manual_verification": False,
            "warnings": [],
            "errors": []
        }

    # CASE 3: CLEAN / UNDAMAGED INFRASTRUCTURE -> Immediate Rejection
    if gate and gate["outcome"] == "NO_CIVIC_ISSUE":
        return {
            "success": True,
            "decision_outcome": "NO_CIVIC_ISSUE",
            "decision_message": "No civic issue found. Please upload an image showing a genuine civic problem.",
            "outcome": "NO_CIVIC_ISSUE",
            "message": "No civic issue found. Please upload an image showing a genuine civic problem.",
            "allow_manual": False,
            "allowManualEntry": False,
            "accepted_as_evidence": False,
            "acceptedAsEvidence": False,
            "aiStatus": "confirmed_clean",
            "ai_status": "confirmed_clean",
            "detected": False,
            "is_civic_issue": False,
            "category": "Road Condition",
            "issue_type": "No Road Defect",
            "title": "No Road Defect",
            "description": "No civic issue found. Please upload an image showing a genuine civic problem.",
            "severity": "None",
            "priority": "None",
            "department": None,
            "department_code": None,
            "departmentCode": None,
            "department_id": None,
            "recommended_department": None,
            "confidence": 0.92,
            "civic_validation": gate.get("civic_validation"),
            "surface_metrics": gate.get("surface_metrics"),
            "road_condition": "clean",
            "primaryDetection": None,
            "detections": [],
            "analysis": {"visualImpactScore": 0.0, "detectionCount": 0, "hasMultipleDetections": False, "allDetections": []},
            "complaint": None,
            "explanation": "No civic issue found. Please upload an image showing a genuine civic problem.",
            "explanation_details": {"reason": "No civic issue found. Please upload an image showing a genuine civic problem."},
            "reviewRequired": False,
            "review_required": False,
            "analysis_id": analysis_id,
            "image_hash": image_hash,
            "model": "civic_validator.pt",
            "detected_features": [],
            "needs_manual_verification": False,
            "warnings": [],
            "errors": []
        }
    explanation_obj = result.get("explanation") or {}
    explanation_text = (
        explanation_obj.get("reason") if isinstance(explanation_obj, dict) and explanation_obj.get("reason")
        else "Defect evaluation completed by local AI vision."
    )
    analysis = result.get("analysis") or {}

    if ai_status == "confirmed_normal" or result.get("condition") == "normal" or result.get("pipe_condition") == "normal":
        cat = None
        title = None
        desc = "The uploaded image shows a normal pipe with no visible leakage or significant damage."
        sev = "None"
        prio = "None"
        dept = None
        dept_code = None
        dept_id = None
        conf = float(result.get("confidence", 0.95))
        needs_manual = False
        detected_class = None
        ai_status = "confirmed_normal"
        has_valid_complaint = False
        explanation_text = "The uploaded image shows a normal pipe with no visible leakage or significant damage."
    elif ai_status == "confirmed_clean" or road_condition == "clean":
        cat = "Road Condition"
        title = "No Road Defect"
        desc = "The uploaded road image shows no visible pothole or significant road defect."
        sev = "None"
        prio = "None"
        dept = None
        dept_code = None
        dept_id = None
        conf = float(result.get("confidence", 0.92))
        needs_manual = False
        detected_class = None
        road_condition = "clean"
        ai_status = "confirmed_clean"
        has_valid_complaint = False
        explanation_text = "The uploaded road image shows no visible pothole or significant road defect."
    elif has_valid_complaint and complaint:
        cat = complaint.get("category", "Roads")
        title = complaint.get("issueType", "Civic Issue")
        desc = complaint.get("description", "Civic issue detected visually by local AI.")
        sev = complaint.get("severity", "High")
        prio = complaint.get("priority", "High")
        dept = complaint.get("departmentName", "Public Works Department")
        dept_code = complaint.get("departmentCode", "PWD")
        dept_id = complaint.get("departmentId", 1)
        conf = float(complaint.get("confidenceScore", result.get("confidence", 0.0)))
        needs_manual = bool(result.get("reviewRequired", ai_status != "confirmed"))
        detected_class = primary.get("class") if primary else title
        if not road_condition:
            road_condition = "defective" if (cat == "Roads" or detected_class == "Pothole") else "non_road"
    elif road_condition == "uncertain":
        cat = "Road Condition"
        title = "Uncertain Road Condition"
        desc = "Road condition could not be verified confidently. Please upload a clearer road image."
        sev = "None"
        prio = "None"
        dept = None
        dept_code = None
        dept_id = None
        conf = float(result.get("confidence", 0.0))
        needs_manual = True
        detected_class = None
        road_condition = "uncertain"
        ai_status = "manual_review"
        has_valid_complaint = False
        explanation_text = "Road condition could not be verified confidently. Please upload a clearer road image."
    elif road_condition == "non_road" or ai_status in ("no_detection", "manual_review"):
        if result.get("department_code") in ("WTR", "DRN", "SAN", "PWD") or result.get("category") in ("Water Supply", "Water", "Drainage", "Sanitation"):
            cat = result.get("category") or ("Water Supply" if result.get("department_code") == "WTR" else "Other")
            title = result.get("issue_type") or result.get("title") or "Pipe Condition Needs Review"
            desc = result.get("message") or result.get("description") or "Pipe condition could not be verified confidently. Please inspect manually."
            sev = result.get("severity") or "Medium"
            prio = result.get("priority") or "Medium"
            dept = result.get("department") or result.get("department_name") or ("Water Supply & Sewerage Board" if result.get("department_code") == "WTR" else None)
            dept_code = result.get("department_code")
            dept_id = result.get("department_id")
            conf = float(result.get("confidence", 0.0))
            needs_manual = True
            detected_class = None
            road_condition = "non_road"
            ai_status = "manual_review"
            has_valid_complaint = False
            explanation_text = desc
        else:
            cat = "Other"
            title = "Manual Review Required"
            desc = result.get("message") or "Uploaded photo does not exhibit recognizable road pavement characteristics."
            sev = "None"
            prio = "None"
            dept = None
            dept_code = None
            dept_id = None
            conf = float(result.get("confidence", 0.0))
            needs_manual = True
            detected_class = None
            road_condition = road_condition or "non_road"
            ai_status = "manual_review"
            has_valid_complaint = False
            explanation_text = "Uploaded photo does not exhibit recognizable road pavement characteristics."
    else:
        cat = "Other Civic Issue"
        title = "Manual Review Required"
        desc = result.get("message") or "Unable to confidently identify a verified civic issue. Please select details manually."
        sev = "None"
        prio = "None"
        dept = None
        dept_code = None
        dept_id = None
        conf = float(result.get("confidence", 0.0))
        needs_manual = True
        detected_class = primary.get("class") if primary else None
        road_condition = road_condition or "uncertain"
        ai_status = "manual_review"
        has_valid_complaint = False

    gate_outcome = gate.get("outcome") if gate else ("VALID_CIVIC_ISSUE" if has_valid_complaint else "CIVIC_ISSUE_UNCERTAIN")
    gate_message = gate.get("message") if gate else ("Civic issue verified and accepted." if has_valid_complaint else "Civic issue detected but classification is uncertain. Manual details enabled for municipal verification.")
    gate_allow_manual = gate.get("allow_manual") if gate else needs_manual
    gate_accepted = gate.get("accepted") if gate else True

    response = {
        # Decision Gate Outcomes
        "decision_outcome": gate_outcome,
        "decision_message": gate_message,
        "outcome": gate_outcome,
        "allow_manual": gate_allow_manual,
        "allowManualEntry": gate_allow_manual,
        "accepted_as_evidence": gate_accepted,
        "acceptedAsEvidence": gate_accepted,
        "civic_validation": gate.get("civic_validation") if gate else None,
        "surface_metrics": gate.get("surface_metrics") if gate else None,

        # Standardized Local Civic AI Agent Schema
        "success": result.get("success", True),
        "road_condition": road_condition,
        "aiStatus": ai_status,
        "ai_status": ai_status,
        "detected": has_valid_complaint,
        "detected_class": detected_class,
        "model": result.get("model") or "civiclens-yolov8",
        "primaryDetection": primary,
        "detections": detections,
        "analysis": analysis,
        "complaint": complaint if has_valid_complaint else None,
        "explanation": explanation_text if isinstance(explanation_text, str) else explanation_obj,
        "explanation_details": explanation_obj,
        "reviewRequired": needs_manual,
        "review_required": needs_manual,
        "transparencyNotice": result.get("transparencyNotice", ""),
        "message": result.get("message", ""),
        "confidence": conf,
        "risk": result.get("risk"),

        # Canonical Response Contract fields
        "category": cat,
        "issue_type": title,
        "title": title,
        "description": desc,
        "severity": sev if sev == "None" else sev.capitalize(),
        "priority": prio if prio == "None" else prio.capitalize(),
        "department": dept,
        "department_code": dept_code,
        "departmentCode": dept_code,
        "department_id": dept_id,
        "recommended_department": dept,

        # Backward compatibility for existing NAGARSETU endpoints & services
        "analysis_id": analysis_id,
        "image_hash": image_hash,
        "is_civic_issue": has_valid_complaint,
        "detected_features": detected_features,
        "needs_manual_verification": needs_manual,
        "reasoningTrace": result.get("reasoningTrace", []),
        "road_analysis": result.get("road_analysis"),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", [])
    }

    return response
