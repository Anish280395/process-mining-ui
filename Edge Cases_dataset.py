import pandas as pd
import random
from datetime import datetime, timedelta

SCENARIO_STEPS = {
    "SCE001": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005"],
    "SCE002": ["PR0010", "PR0011", "PR0012", "PR0013", "PR0014"],
}

SCENARIO_FLAGS = {
    "SCE001": {"Export Flag": 1, "Dangerous Flag": 1},
    "SCE002": {"Export Flag": 2, "Dangerous Flag": 2},
}

def generate_duplicate_steps(steps):
    steps = steps.copy()
    if steps:
        duplicate = random.choice(steps)
        insert_at = random.randint(0, len(steps))
        steps.insert(insert_at, duplicate)
    return steps

def generate_missing_endpoints(steps):
    steps = steps.copy()
    if steps:
        if random.random() < 0.5:
            steps.pop(0)
        else:
            steps.pop(-1)
    return steps

def generate_fully_shuffled_steps(steps):
    steps = steps.copy()
    random.shuffle(steps)
    return steps

def generate_with_junk_steps(steps):
    steps = steps.copy()
    junk_steps = [f"JUNK{random.randint(100, 999)}" for _ in range(2)]
    insert_at = random.randint(0, len(steps))
    return steps[:insert_at] + junk_steps + steps[insert_at:]

def generate_edge_case_dataset(num_orders=100, generator_fn=None):
    data = []
    scenarios = list(SCENARIO_STEPS.keys())
    base_start = datetime(2025, 7, 15, 8, 0, 0)

    for i in range(num_orders):
        order_id = f"ORD{i+1:04d}"
        customer_id = f"CUS{random.randint(1, 20):04d}"
        item_id = f"ITE{random.randint(1, 50):04d}"

        scenario = random.choice(scenarios)
        export_flag = SCENARIO_FLAGS[scenario]["Export Flag"]
        dangerous_flag = SCENARIO_FLAGS[scenario]["Dangerous Flag"]
        planned_steps = SCENARIO_STEPS[scenario]

        if generator_fn:
            actual_steps = generator_fn(planned_steps)
        else:
            actual_steps = planned_steps.copy()

        step_duration = timedelta(minutes=10)
        planned_start_time = base_start + timedelta(days=i)

        planned_times = [
            (planned_start_time + idx * step_duration, planned_start_time + (idx + 1) * step_duration)
            for idx in range(len(planned_steps))
        ]

        actual_start_time = planned_start_time
        actual_times = [
            (actual_start_time + idx * step_duration, actual_start_time + (idx + 1) * step_duration)
            for idx in range(len(actual_steps))
        ]

        for idx, step in enumerate(planned_steps):
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
    cases = [
        ("dataset_duplicates.csv", generate_duplicate_steps),
        ("dataset_missing_endpoints.csv", generate_missing_endpoints),
        ("dataset_fully_shuffled.csv", generate_fully_shuffled_steps),
        ("dataset_with_junk.csv", generate_with_junk_steps),
    ]

    for filename, generator in cases:
        df = generate_edge_case_dataset(100, generator_fn=generator)
        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")
