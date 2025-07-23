import pandas as pd
import random

# Standard process steps (matching your codes)
STANDARD_STEPS = [
    "PR0001", "PR0002", "PR0003", "PR0004",
    "PR0005", "PR0006", "PR0007", "PR0008",
    "PR0009", "PR0010", "PR0011", "PR0012"
]

def generate_neat_steps():
    return STANDARD_STEPS.copy()

def generate_out_of_order_steps():
    steps = STANDARD_STEPS.copy()
    i, j = random.sample(range(len(steps)), 2)
    steps[i], steps[j] = steps[j], steps[i]
    return steps

def generate_boomer_steps():
    steps = STANDARD_STEPS.copy()
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
    for i in range(num_records):
        order_id = f"ORD{i+1:04d}"
        customer_id = f"CUS{random.randint(1,20):04d}"
        item_id = f"ITE{random.randint(1,50):04d}"
        export_flag = random.choice([1, 2])
        dangerous_flag = random.choice([1, 2])
        derived_scenario = "SCE001"
        scenario_used = "SCE001"

        planned = generate_neat_steps()

        if not mix:
            as_is = planned.copy()
        else:
            r = random.random()
            if r < 0.7:
                as_is = planned.copy()  # neat
            elif r < 0.9:
                as_is = generate_out_of_order_steps()
            else:
                as_is = generate_boomer_steps()

        data.append({
            "Order ID": order_id,
            "Customer ID": customer_id,
            "Item ID": item_id,
            "Export Flag": export_flag,
            "Dangerous Flag": dangerous_flag,
            "Derived Scenario": derived_scenario,
            "Scenario Used": scenario_used,
            "Planned Steps": steps_to_str(planned),
            "As Is Steps": steps_to_str(as_is)
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    neat_df = generate_dataset(100, mix=False)
    neat_df.to_csv("dataset_neat.csv", index=False)
    print("Saved 100% neat dataset to dataset_neat.csv")

    mixed_df = generate_dataset(100, mix=True)
    mixed_df.to_csv("dataset_mixed.csv", index=False)
    print("Saved mixed dataset (70/20/10) to dataset_mixed.csv")