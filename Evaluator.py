import json

# -------------------------------
# HELPERS
# -------------------------------
def normalize(text):
    return str(text).lower().strip() if text else ""


def extract_number(value):
    import re
    nums = re.findall(r"\d+", str(value))
    return int(nums[0]) if nums else None


# -------------------------------
# CORE COMPLIANCE ENGINE
# -------------------------------
def evaluate_tender(tender: dict, manufacturer: dict):

    results = []
    total_score = 0
    max_score = 0
    critical_failure = False

    # -------------------------------
    # CONFIG (can be moved to JSON later)
    # -------------------------------
    rules = {
        "product_type": {"type": "exact", "weight": 20, "critical": True},
        "voltage": {"type": "exact", "weight": 15, "critical": True},
        "current": {"type": "min", "weight": 20, "critical": True},
        "features": {"type": "list", "weight": 10, "critical": False}
    }

    # -------------------------------
    # PRODUCT TYPE
    # -------------------------------
    req = "product_type"
    max_score += rules[req]["weight"]

    t_val = normalize(tender.get(req))
    m_val = normalize(manufacturer.get(req))

    if t_val == m_val:
        total_score += rules[req]["weight"]
        status = "Compliant"
    else:
        status = "Non-Compliant"
        critical_failure = True

    results.append({
        "parameter": req,
        "required": t_val,
        "vendor": m_val,
        "status": status,
        "reason": "" if status == "Compliant" else "Product type mismatch"
    })

    # -------------------------------
    # VOLTAGE
    # -------------------------------
    req = "voltage"
    max_score += rules[req]["weight"]

    t_val = normalize(tender.get(req))
    m_val = normalize(manufacturer.get(req))

    if t_val == m_val:
        total_score += rules[req]["weight"]
        status = "Compliant"
    else:
        status = "Non-Compliant"
        critical_failure = True

    results.append({
        "parameter": req,
        "required": t_val,
        "vendor": m_val,
        "status": status,
        "reason": "" if status == "Compliant" else "Voltage mismatch"
    })

    # -------------------------------
    # CURRENT (>= logic)
    # -------------------------------
    req = "current"
    max_score += rules[req]["weight"]

    t_val = extract_number(tender.get(req))
    m_val = extract_number(manufacturer.get(req))

    if m_val is not None and t_val is not None and m_val >= t_val:
        total_score += rules[req]["weight"]
        status = "Compliant"
        reason = ""
    else:
        status = "Non-Compliant"
        reason = "Vendor current lower than required"
        critical_failure = True

    results.append({
        "parameter": req,
        "required": t_val,
        "vendor": m_val,
        "status": status,
        "reason": reason
    })

    # -------------------------------
    # FEATURES (partial scoring)
    # -------------------------------
    req = "features"
    max_score += rules[req]["weight"]

    t_features = set(map(normalize, tender.get(req, [])))
    m_features = set(map(normalize, manufacturer.get(req, [])))

    matched = t_features & m_features

    if t_features:
        feature_score = int((len(matched) / len(t_features)) * rules[req]["weight"])
    else:
        feature_score = 0

    total_score += feature_score

    results.append({
        "parameter": req,
        "required": list(t_features),
        "vendor": list(m_features),
        "matched": list(matched),
        "status": "Partial" if matched else "Non-Compliant",
        "score": feature_score
    })

    # -------------------------------
    # FINAL DECISION
    # -------------------------------
    percentage = (total_score / max_score) * 100 if max_score else 0

    if critical_failure:
        final_status = "REJECTED"
    elif percentage >= 80:
        final_status = "APPROVED"
    elif percentage >= 60:
        final_status = "CONDITIONAL"
    else:
        final_status = "REJECTED"

    # -------------------------------
    # FINAL OUTPUT
    # -------------------------------
    return {
        "status": final_status,
        "score": round(percentage, 2),
        "total_score": total_score,
        "max_score": max_score,
        "details": results
    }