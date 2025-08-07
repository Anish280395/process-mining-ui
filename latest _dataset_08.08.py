import pandas as pd
import random
from datetime import datetime, timedelta

# Reference scenario mapping (same as backend)
SCENARIO_STEPS = {
    "SCE001": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE002": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0006", "PR0007", "PR0013", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE003": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE004": ["PR0001", "PR0002", "PR0003", "PR0004", "PR0005", "PR0014", "PR0006", "PR0007", "PR0008", "PR0013", "PR0009", "PR0010", "PR0011", "PR0012"],
    "SCE005": ["PR0001", "PR0003", "PR0004", "PR0014", "PR0012", "PR0006"],
}

SCENARIO_LIST = list(SCENARIO_STEPS.keys())

def random_scenario():
    return random.choice(SCENARIO_LIST)

def make_actual_steps(planned_steps, breach_type):
    steps = planned_steps.copy()

    if breach_type == "none":
        return steps
    elif breach_type == "missing":
        remove = random.choice(steps)
        steps.remove(remove)
        return steps
    elif breach_type == "extra":
        pos = random.randint(0, len(steps))
        steps = steps[:pos] + [f"JUNK{random.randint(100,999)}"] + steps[pos:]
        return steps
    elif breach_type == "duplicate":
        dup = random.choice(steps)
        pos = random.randint(0, len(steps))
        steps = steps[:pos] + [dup] + steps[pos:]
        return steps
    elif breach_type == "out_of_order":
        if len(steps) >= 2:
            i, j = random.sample(range(len(steps)), 2)
            steps[i], steps[j] = steps[j], steps[i]
        return steps
    elif breach_type == "worst":
        # Remove one, add extra, add duplicate, shuffle some
        if len(steps) >= 3:
            remove = random.choice(steps)
            steps.remove(remove)
            extra = f"JUNK{random.randint(100,999)}"
            pos = random.randint(0, len(steps))
            steps = steps[:pos] + [extra] + steps[pos:]
            dup = random.choice(steps)
            steps.insert(random.randint(0, len(steps)), dup)
            # Shuffle three
            idxs = random.sample(range(len(steps)), 3)
            a, b, c = idxs
            steps[a], steps[b], steps[c] = steps[c], steps[a], steps[b]
        return steps
    else:
        return steps

def make_row(order_id, item_id, customer_id, scenario, step_idx, planned_step, planned_start, actual_steps, step_duration=10):
    # Try to match actual step for this planned step, else fill blanks
    as_is_pos_no, as_is_step_id, as_is_start, as_is_end = None, None, None, None
    if planned_step in actual_steps:
        actual_idx = actual_steps.index(planned_step)
        as_is_pos_no = actual_idx + 1
        as_is_step_id = planned_step
        as_is_start = planned_start + timedelta(minutes=step_duration*actual_idx)
        as_is_end = as_is_start + timedelta(minutes=step_duration)
    row = {
        "Order-No.": order_id,
        "Customer-No.": customer_id,
        "Item-No.": item_id,
        "Export to not EU [1 = n, 2 = y]": random.randint(1,2),
        "Dangerous Good [1 = n, 2 = y]": random.randint(1,2),
        "Planed-Master-Scenario-No.": scenario,
        "Planed-Master-Order-Processing-Ongoing Position No.": step_idx + 1,
        "Planed-Master-Order-Processing-Position-No. as an ID": planned_step,
        "Planed-Master-Order-Processing-Start-Time": planned_start + timedelta(minutes=step_duration*step_idx),
        "Planed-Master-Order-Processing-End-Time": planned_start + timedelta(minutes=step_duration*(step_idx+1)),
        "As-Is-Real-Order-Processing-Ongoing Position No.": as_is_pos_no,
        "As-Is-Master-Order-Processing-Position-No. as an ID": as_is_step_id,
        "As-Is-Real-Order-Processing-Start-Time": as_is_start,
        "As-Is-Real-Order-Processing-End-Time": as_is_end,
        "Final Yield Quantity": 24,
        "Total Scrap Quantity": 0
    }
    return row

def generate_test_dataset():
    rows = []
    base_start = datetime(2025, 8, 7, 8, 0)
    order_id = 1
    # 1 case for each scenario and each breach type
    breach_types = ["none", "missing", "extra", "duplicate", "out_of_order", "worst"]
    for scenario in SCENARIO_LIST:
        planned_steps = SCENARIO_STEPS[scenario]
        for breach_type in breach_types:
            item_id = f"ITM{order_id:04d}"
            customer_id = f"CUST{random.randint(1,20):04d}"
            planned_start = base_start + timedelta(days=order_id)
            actual_steps = make_actual_steps(planned_steps, breach_type)
            # Generate a row for each planned step (for full groupby compatibility)
            for idx, planned_step in enumerate(planned_steps):
                row = make_row(f"ORD{order_id:04d}", item_id, customer_id, scenario, idx, planned_step, planned_start, actual_steps)
                rows.append(row)
            order_id += 1

        # Also, add a "random combo" edge case for each scenario
        for combo in range(2):
            breach_types_combo = random.sample(breach_types[1:], 3) # e.g. missing + extra + out_of_order
            actual = planned_steps.copy()
            for t in breach_types_combo:
                actual = make_actual_steps(actual, t)
            item_id = f"ITM{order_id:04d}"
            customer_id = f"CUST{random.randint(1,20):04d}"
            planned_start = base_start + timedelta(days=order_id)
            for idx, planned_step in enumerate(planned_steps):
                row = make_row(f"ORD{order_id:04d}", item_id, customer_id, scenario, idx, planned_step, planned_start, actual)
                rows.append(row)
            order_id += 1

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = generate_test_dataset()
    df.to_csv("test_breach_cases.csv", index=False)
    print("Generated test_breach_cases.csv with all scenario and breach cases!")