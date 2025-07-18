import csv
import random


scenario_data = {
    (1,1): ("SCE001", 12),  # Normal
    (1,2): ("SCE002", 13),  # Danger
    (2,1): ("SCE003", 13),  # Custom
    (2,2): ("SCE004", 14),  # Danger + Custom
}

# Base process steps
base_steps = [f'PR{str(i).zfill(4)}' for i in range(1, 13)]
danger_step = "PR0013"
custom_step = "PR0014"

def get_planned_steps(scenario):
    steps = base_steps.copy()
    if scenario == "SCE002":
        steps.append(danger_step)
    elif scenario == "SCE003":
        steps.append(custom_step)
    elif scenario == "SCE004":
        steps += [danger_step, custom_step]
    return steps

def simulate_as_is(planned, breach_type):
    as_is = planned.copy()
    if breach_type == "missing" and len(as_is) > 1:
        as_is.pop(random.randint(0, len(as_is)-1))
    elif breach_type == "out of order":
        random.shuffle(as_is)
    return as_is

def find_missing(planned, actual):
    return [step for step in planned if step not in actual]

def find_out_of_order(planned, actual):
    return [f"{p}≠{a}" for p, a in zip(planned, actual) if p != a]

# data
customer_ids = ["CUS3636", "CUS3637", "CUS3638", "CUS3639", "CUS3640"]
item_ids = ["ITE5151", "ITE5152", "ITE5153", "ITE5154", "ITE5155", "ITE5156"]

rows = []
order_number_start = 4711

for i in range(50):
    order_id = f"ORD{order_number_start + i}"
    customer_id = random.choice(customer_ids)

    for _ in range(3):  # 3 items per order
        item_id = random.choice(item_ids)
        export_flag = random.choice([1, 2])
        danger_flag = random.choice([1, 2])

        derived_scenario, _ = scenario_data[(export_flag, danger_flag)]
        planned = get_planned_steps(derived_scenario)

        # 25% chance for boomer exception
        is_boomer = random.random() < 0.25
        breach_type = "None"
        breach_details = "No breach"
        scenario_used = derived_scenario
        as_is = planned.copy()

        if is_boomer:
            scenario_used = "SCE005"
            breach_type = random.choice(["missing", "out of order"])
            as_is = simulate_as_is(planned, breach_type)
            if breach_type == "missing":
                missing = find_missing(planned, as_is)
                breach_details = f"Missing: {', '.join(missing)}"
            else:
                mismatch = find_out_of_order(planned, as_is)
                breach_details = f"Wrong order: {', '.join(mismatch)}"

        rows.append([
            order_id, customer_id, item_id,
            export_flag, danger_flag,
            derived_scenario, scenario_used,
            '|'.join(planned), '|'.join(as_is),
            breach_type, breach_details
        ])

# to CSV
with open("sample_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Order ID", "Customer ID", "Item ID",
        "Export Flag", "Dangerous Flag",
        "Derived Scenario", "Scenario Used",
        "Planned Steps", "As-Is Steps",
        "Breach Type", "Breach Details"
    ])
    writer.writerows(rows)

print("CSV generated successfully!")