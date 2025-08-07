import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import difflib

# --- Canonical scenario step mapping (from your reference) ---
SCENARIO_STEPS = {
    "SCE001": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE002": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0013", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE003": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE004": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0013", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE005": ["PR0001", "PR0003", "PR0004", "PR0014", "PR0012", "PR0006"],
}

CORPORATE_COLORS = {
    "blue": "#2b6cb0",
    "green": "#48bb78",
    "red": "#f56565",
    "orange": "#ed8936",
    "yellow": "#ecc94b",
    "gray": "#CBD5E0"
}

plt.rcParams.update({
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.labelcolor": "#2d3748",
    "axes.edgecolor": "#CBD5E0",
    "xtick.color": "#2d3748",
    "ytick.color": "#2d3748",
    "grid.color": "#CBD5E0",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "figure.facecolor": "white",
    "axes.facecolor": "white"
})

def detect_breaches(planned, actual):
    # 1. Missing steps: In planned, not in actual
    missing_steps = [step for step in planned if step not in actual]

    # 2. Extra steps: In actual, not in planned
    extra_steps = [step for step in actual if step not in planned]

    # 3. Duplicate steps: Any step in actual >1 and also present in planned
    actual_counts = Counter(actual)
    duplicates = [step for step, cnt in actual_counts.items() if cnt > 1 and step in planned]

    # 4. Out-of-order detection (using SequenceMatcher)
    sm = difflib.SequenceMatcher(None, planned, [x for x in actual if x in planned])
    out_of_order_steps = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete", "insert"):
            out_of_order_steps += planned[i1:i2]

    return missing_steps, out_of_order_steps, extra_steps, duplicates

def generate_breach_plot(results):
    type_counts = {"Missing": 0, "Out of Order": 0, "Both": 0, "None": 0}
    for r in results:
        missing = len(r.get("Missing_Steps", []))
        out_of_order = len(r.get("Out_of_Order_Steps", []))
        if missing > 0 and out_of_order > 0:
            type_counts["Both"] += 1
        elif missing > 0:
            type_counts["Missing"] += 1
        elif out_of_order > 0:
            type_counts["Out of Order"] += 1
        else:
            type_counts["None"] += 1
    total_orders = sum(type_counts.values()) if sum(type_counts.values()) > 0 else 1
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [
        CORPORATE_COLORS["red"],
        CORPORATE_COLORS["orange"],
        CORPORATE_COLORS["yellow"],
        CORPORATE_COLORS["green"]
    ]
    bars = ax.bar(type_counts.keys(), type_counts.values(), color=colors)
    ax.set_title("Breach Type Frequency")
    ax.set_ylabel("Number of Orders")
    ax.set_xlabel("Breach Type")
    ax.grid(axis="y")
    for bar, label in zip(bars, type_counts.keys()):
        height = bar.get_height()
        percentage = (height / total_orders) * 100
        ax.annotate(f'{height} ({percentage:.1f}%)',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', color="#2d3748", fontsize=10)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", facecolor="white")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

def calculate_quantity_deviation(yield_qty, scrap_qty):
    total = yield_qty + scrap_qty
    return (scrap_qty / total * 100) if total > 0 else 0.0
