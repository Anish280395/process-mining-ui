import matplotlib.pyplot as plt
import io
import base64

def detect_breaches(expected, actual):
    expected_set = set(expected)
    actual_set = set(actual)

    missing_steps = list(expected_set - actual_set)
    out_of_order_steps = []

    min_len = min(len(expected), len(actual))
    for i in range(min_len):
        if expected[i] != actual[i]:
            out_of_order_steps.append(f"{expected[i]}≠{actual[i]}")

    return missing_steps, out_of_order_steps

def generate_breach_plot(results):
    type_counts = { "Missing": 0, "Out of Order": 0, "Both": 0, "None": 0 }

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

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ['#f56565', '#ed8936', '#ecc94b', '#48bb78']  # Red, Orange, Yellow, Green
    bars = ax.bar(type_counts.keys(), type_counts.values(), color=colors)
    ax.set_title("Breach Type Frequency", fontsize=14, color="#2d3748")
    ax.set_ylabel("Number of Orders")
    ax.set_xlabel("Breach Type")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.tick_params(colors="#2d3748")

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', color="#2d3748")

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{encoded}"
