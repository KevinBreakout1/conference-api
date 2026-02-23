APPROVED_LABEL_MAP = {
    # Healthcare
    "medical": "Healthcare",
    "health": "Healthcare",
    "biotech": "Healthcare",

    # Finance
    "finance": "Finance",
    "banking": "Finance",
    "business": "Finance",

    # Legal
    "legal": "Legal",
    "law": "Legal",

    # Logistics
    "logistics": "Logistics",
    "transport": "Logistics",
    "supply-chain": "Logistics",

    # Human Resources
    "human-resources": "Human Resources",
    "workforce": "Human Resources",
    "recruiting": "Human Resources",
}


KEYWORD_FALLBACK = {
    "Finance": ["finance", "bank", "investment", "capital", "fintech"],
    "Healthcare": ["health", "medical", "clinical", "hospital", "pharma"],
    "Legal": ["legal", "law", "attorney", "litigation", "compliance"],
    "Logistics": ["logistics", "freight", "shipping", "supply chain"],
    "Human Resources": ["human resources", "hr", "recruiting", "talent", "workforce"],
}


def map_industry(event):
    """
    Hybrid industry classification:
    1) Try structured phq_labels
    2) Fallback to keyword scanning
    """

    # --- Structured label matching ---
    labels = event.get("phq_labels") or []

    for label_obj in labels:
        label = (label_obj.get("label") or "").lower()
        if label in APPROVED_LABEL_MAP:
            return APPROVED_LABEL_MAP[label]

    # --- Fallback keyword scan ---
    title = (event.get("title") or "").lower()
    description = (event.get("description") or "").lower()
    text_blob = f"{title} {description}"

    for industry, keywords in KEYWORD_FALLBACK.items():
        for keyword in keywords:
            if keyword in text_blob:
                return industry

    return None
