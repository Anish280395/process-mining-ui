import pandas as pd
import random

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

def steps_to_str(steps):
    return "|".join(steps)

def generate_dataset(num_records=100, mix=False):
    data = []
    scenarios = list(SCENARIO_STEPS.keys())
    for i in range(num_records):
        order_id = f"ORD{i+1:04d}"
        customer_id = f"CUS{random.randint(1,20):04d}"
        item_id = f"ITE{random.randint(1,50):04d}"

        scenario = random.choice(scenarios)
        export_flag = SCENARIO_FLAGS[scenario]["Export Flag"]
        dangerous_flag = SCENARIO_FLAGS[scenario]["Dangerous Flag"]

        planned_steps = SCENARIO_STEPS[scenario]

        if not mix:
            as_is_steps = generate_neat_steps(planned_steps)
        else:
            r = random.random()
            if r < 0.7:
                as_is_steps = generate_neat_steps(planned_steps)
            elif r < 0.9:
                as_is_steps = generate_out_of_order_steps(planned_steps)
            else:
                as_is_steps = generate_boomer_steps(planned_steps)

        data.append({
            "Order ID": order_id,
            "Customer ID": customer_id,
            "Item ID": item_id,
            "Export Flag": export_flag,
            "Dangerous Flag": dangerous_flag,
            "Derived Scenario": scenario,
            "Scenario Used": scenario,
            "Planned Steps": steps_to_str(planned_steps),
            "As Is Steps": steps_to_str(as_is_steps),
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    neat_df = generate_dataset(100, mix=False)
    neat_df.to_csv("dataset_neat.csv", index=False)
    print("Saved neat dataset with scenario-specific steps to dataset_neat.csv")

    mixed_df = generate_dataset(100, mix=True)
    mixed_df.to_csv("dataset_mixed.csv", index=False)
    print("Saved mixed dataset with scenario-specific steps to dataset_mixed.csv")