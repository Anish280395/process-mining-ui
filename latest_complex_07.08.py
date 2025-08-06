import pandas as pd
import random
from datetime import datetime, timedelta

SCENARIO_STEPS = {
    "SCE001": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE002": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0013", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE003": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE004": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0013", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE005": ["PR0001", "PR0003", "PR0004", "PR0014", "PR0012", "PR0006"],
}

SCENARIO_FLAGS = {
    "SCE001": {"Export Flag": 1, "Dangerous Flag": 1},
    "SCE002": {"Export Flag": 1, "Dangerous Flag": 2},
    "SCE003": {"Export Flag": 2, "Dangerous Flag": 1},
    "SCE004": {"Export Flag": 2, "Dangerous Flag": 2},
    "SCE005": {"Export Flag": 2, "Dangerous Flag": 2},
}

# ----------- Step manipulation functions -----------
def generate_neat_steps(steps): return steps.copy()

def generate_out_of_order_steps(steps):
    steps = steps.copy()
    if len(steps) > 1:
        i, j = random.sample(range(len(steps)), 2)
        steps[i], steps[j] = steps[j], steps[i]
    return steps

def generate_missing_steps(steps):
    steps = steps.copy()
    if len(steps) > 0:
        missing = random.choice(steps)
        steps.remove(missing)
    return steps

def generate_extra_steps(steps):
    steps = steps.copy()
    junk = [f"JUNK{random.randint(100, 999)}" for _ in range(random.randint(1, 2))]
    insert_at = random.randint(0, len(steps))
    return steps[:insert_at] + junk + steps[insert_at:]

def generate_duplicate_steps(steps):
    steps = steps.copy()
    if steps:
        dup = random.choice(steps)
        steps.insert(random.randint(0, len(steps)), dup)
    return steps

# ----------- Dataset generator -----------
def generate_dataset(num_orders=100, mode="neat"):
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

        # --- Determine actual steps based on mode ---
        if mode == "neat":
            actual_steps = generate_neat_steps(planned_steps)
        elif mode == "mixed":
            r = random.random()
            if r < 0.6: actual_steps = generate_neat_steps(planned_steps)
            elif r < 0.8: actual_steps = generate_out_of_order_steps(planned_steps)
            else: actual_steps = generate_missing_steps(planned_steps)
        elif mode == "missing":
            actual_steps = generate_missing_steps(planned_steps)
        elif mode == "out_of_order":
            actual_steps = generate_out_of_order_steps(planned_steps)
        elif mode == "extra":
            actual_steps = generate_extra_steps(planned_steps)
        elif mode == "duplicates":
            actual_steps = generate_duplicate_steps(planned_steps)
        elif mode == "delayed":
            actual_steps = generate_neat_steps(planned_steps)
        elif mode == "quantity":
            actual_steps = generate_neat_steps(planned_steps)
        elif mode == "complex":
            # Randomly apply multiple manipulations
            actual_steps = generate_neat_steps(planned_steps)
            if random.random() < 0.4:
                actual_steps = generate_missing_steps(actual_steps)
            if random.random() < 0.4:
                actual_steps = generate_out_of_order_steps(actual_steps)
            if random.random() < 0.3:
                actual_steps = generate_extra_steps(actual_steps)
            if random.random() < 0.2:
                actual_steps = generate_duplicate_steps(actual_steps)
        else:
            actual_steps = planned_steps.copy()

        # Duration handling
        step_duration = timedelta(minutes=10)
        if mode == "delayed" or (mode == "complex" and random.random() < 0.3):
            step_duration = timedelta(minutes=random.randint(15, 25))  # Delay steps

        planned_start_time = base_start + timedelta(days=i)
        planned_times = [(planned_start_time + idx * timedelta(minutes=10),
                           planned_start_time + (idx + 1) * timedelta(minutes=10))
                          for idx in range(len(planned_steps))]

        actual_start_time = planned_start_time
        actual_times = [(actual_start_time + idx * step_duration,
                          actual_start_time + (idx + 1) * step_duration)
                         for idx in range(len(actual_steps))]

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

            final_yield = 24
            scrap_qty = 0
            if mode == "quantity" or (mode == "complex" and random.random() < 0.3):
                final_yield = random.randint(15, 23)
                scrap_qty = 24 - final_yield

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
                "Final Yield Quantity": final_yield,
                "Total Scrap Quantity": scrap_qty,
            }
            data.append(row)
    return pd.DataFrame(data)

if __name__ == "__main__":
    modes = [
        ("neat", "dataset_neat_long_07.08.csv"),
        ("mixed", "dataset_mixed_long_07.08.csv"),
        ("missing", "dataset_missing_steps_07.08.csv"),
        ("out_of_order", "dataset_out_of_order_07.08.csv"),
        ("extra", "dataset_extra_steps_07.08.csv"),
        ("duplicates", "dataset_duplicates_07.08.csv"),
        ("delayed", "dataset_delayed_07.08.csv"),
        ("quantity", "dataset_quantity_issues_07.08.csv"),
        ("complex", "dataset_complex_07.08.csv"),
    ]
    for mode, filename in modes:
        df = generate_dataset(100, mode=mode)
        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")
