import pandas as pd
import random
from datetime import datetime, timedelta

SCENARIO_STEPS = {
    "SCE001": [
        "PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006",
        "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"
    ],
    "SCE002": [
        "PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006",
        "PR0007", "PR0013", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"
    ],
    "SCE003": [
        "PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014",
        "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"
    ],
    "SCE004": [
        "PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014",
        "PR0006", "PR0007", "PR0008", "PR0013", "PR0009", "PR0010",
        "PR0011", "PR0012"
    ],
    "SCE005": [
        "PR0001", "PR0003", "PR0004", "PR0014", "PR0012", "PR0006"
    ],
}

SCENARIO_FLAGS = {
    "SCE001": {"Export Flag": 1, "Dangerous Flag": 1},
    "SCE002": {"Export Flag": 1, "Dangerous Flag": 2},
    "SCE003": {"Export Flag": 2, "Dangerous Flag": 1},
    "SCE004": {"Export Flag": 2, "Dangerous Flag": 2},
    "SCE005": {"Export Flag": 2, "Dangerous Flag": 2},
}

def generate_neat_steps(steps):
    return steps.copy()

def generate_out_of_order_steps(steps):
    steps = steps.copy()
    if len(steps) > 1:
        i, j = random.sample(range(len(steps)), 2)
        steps[i], steps[j] = steps[j], steps[i]
    return steps

def generate_boomer_steps(steps):
    steps = steps.copy()
    if len(steps) > 0:
        missing = random.choice(steps)
        steps.remove(missing)
    if len(steps) > 1:
        i, j = random.sample(range(len(steps)), 2)
        steps[i], steps[j] = steps[j], steps[i]
    return steps

def generate_long_format_dataset(num_orders=100, mix=False):
    data = []
    scenarios = list(SCENARIO_STEPS.keys())
    base_start = datetime(2025, 7, 15, 8, 0, 0)  # fixed start time

    for i in range(num_orders):
        order_id = f"ORD{i+1:04d}"
        customer_id = f"CUS{random.randint(1,20):04d}"
        item_id = f"ITE{random.randint(1,50):04d}"

        scenario = random.choice(scenarios)
        export_flag = SCENARIO_FLAGS[scenario]["Export Flag"]
        dangerous_flag = SCENARIO_FLAGS[scenario]["Dangerous Flag"]
        planned_steps = SCENARIO_STEPS[scenario]

        if not mix:
            actual_steps = generate_neat_steps(planned_steps)
        else:
            r = random.random()
            if r < 0.7:
                actual_steps = generate_neat_steps(planned_steps)
            elif r < 0.9:
                actual_steps = generate_out_of_order_steps(planned_steps)
            else:
                actual_steps = generate_boomer_steps(planned_steps)

        step_duration = timedelta(minutes=10)
        planned_start_time = base_start + timedelta(days=i)

        # Calculate planned timestamps
        planned_times = [
            (planned_start_time + idx * step_duration, planned_start_time + (idx + 1) * step_duration)
            for idx in range(len(planned_steps))
        ]

        # Calculate actual timestamps aligned with actual steps
        actual_start_time = planned_start_time
        actual_times = [
            (actual_start_time + idx * step_duration, actual_start_time + (idx + 1) * step_duration)
            for idx in range(len(actual_steps))
        ]

        for idx, step in enumerate(planned_steps):
            # Find actual position for planned step if exists
            if step in actual_steps:
                actual_idx = actual_steps.index(step)
                as_is_pos_no = actual_idx + 1
                as_is_step_id = step
                actual_start, actual_end = actual_times[actual_idx]
            else:
                as_is_pos_no = None
                as_is_step_id = None
                actual_start = None
                actual_end = None

            row = {
                "Order-No.": order_id,
                "Customer-No.": customer_id,
                "Item-No.": item_id,
                "Export to not EU [1 = n, 2 = y]": export_flag,
                "Dangerous Good [1 = n, 2 = y]": dangerous_flag,
                "Planed-Master-Scenario-No.": scenario,
                "Planed-Master-Order-Processing-Ongoing Position No.": idx + 1,
                "Planed-Master-Order-Processing-Position-No. as an ID": step,
                "Planed-Master-Order-Processing-Start-Time": planned_times[idx][0],
                "Planed-Master-Order-Processing-End-Time": planned_times[idx][1],
                "As-Is-Real-Order-Processing-Ongoing Position No.": as_is_pos_no,
                "As-Is-Master-Order-Processing-Position-No. as an ID": as_is_step_id,
                "As-Is-Real-Order-Processing-Start-Time": actual_start,
                "As-Is-Real-Order-Processing-End-Time": actual_end,
                "Final Yield Quantity": 24,
                "Total Scrap Quantity": 0,
            }
            data.append(row)

    return pd.DataFrame(data)

if __name__ == "__main__":
    neat_df = generate_long_format_dataset(100, mix=False)
    neat_df.to_csv("dataset_neat_long.csv", index=False)
    print("Saved neat long-format dataset to dataset_neat_long.csv")

    mixed_df = generate_long_format_dataset(100, mix=True)
    mixed_df.to_csv("dataset_mixed_long.csv", index=False)
    print("Saved mixed long-format dataset to dataset_mixed_long.csv")