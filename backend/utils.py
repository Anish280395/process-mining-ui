import matplotlib.pyplot as plt
import io
import base64


STANDARD_STEPS = [
    ("PR0001", "Issuance of RFQ"),
    ("PR0002", "Technical Evaluation"),
    ("PR0003", "Commercial Evaluation"),
    ("PR0004", "PO Creation"),
    ("PR0005", "Production Planning"),
    ("PR0006", "Parts Manufacturing"),
    ("PR0007", "Packaging & Dispatch"),
    ("PR0008", "Goods In Transit"),
    ("PR0009", "Goods Receipt at Warehouse"),
    ("PR0010", "Quality Inspection"),
    ("PR0011", "Invoice Generation"),
    ("PR0012", "Payment Clearance"),
]

def get_expected_steps(export_flag, dangerous_flag):
    steps = [code for code, _ in STANDARD_STEPS]

    if dangerous_flag == 2:
        steps.append("PR0013")  # Additional step for dangerous items
    if export_flag == 2:
        steps.append("PR0014") # Customs step
    
    return steps

def detect_breaches(expected, actual):
    expected_set = set(expected)
    actual_set = set(actual)

    missing_steps = list(expected_set - actual_set)
    out_of_order_steps = []

    for i in range(min(len(expected), len(actual))):
        if expected[i] != actual[i]:
            out_of_order_steps.append(f"{expected[i]}≠{actual[i]}")
    
    return missing_steps, out_of_order_steps

def generate_breach_plot(results):
    type_counts = { "Missing": 0, "Out of Order": 0, "Both":0, "None": 0 }

    for r in results:
        missing = r.get("Missing steps", [])
        out_of_order = r.get("Out of Order Steps", [])

        if missing and out_of_order:
            type_counts["Both"] += 1
        elif missing:
            type_counts["Missing"] += 1
        elif out_of_order:
            type_counts["Out of Order"] += 1
        else:
            type_counts["None"] += 1

        
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(type_counts.keys(), type_counts.values(), color='tomato')
    ax.set_title("Breach Type Frequency")
    ax.set_ylabel("Number of Orders")
    ax.set_xlabel("Breach Type")
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    # Convert chart to base64
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"data:image/png;base64,{encoded}"