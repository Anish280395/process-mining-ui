from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from backend.utils import get_expected_steps, detect_breaches, generate_breach_plot
import os

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze_csv():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        df = pd.read_csv(file)

        required_columns = {
            "Order ID", "Customer ID", "Item ID",
            "Export Flag", "Dangerous Flag",
            "Derived Scenario", "Scenario Used",
            "Planned Steps", "As Is Steps"
        }

        if not required_columns.issubset(df.columns):
            return jsonify({"error": f"CSV must include columns: {', '.join(required_columns)}"}), 400

        results = []

        for _, row in df.iterrows():
            order_id = row['Order ID']
            customer_id = row['Customer ID']
            item_id = row['Item ID']
            export_flag = int(row['Export Flag'])
            dangerous_flag = int(row['Dangerous Flag'])
            derived_scenario = row['Derived Scenario']
            scenario_used = row['Scenario Used']
            planned_steps = row['Planned Steps'].split('|')
            as_is_steps = row['As Is Steps'].split('|')

            missing_steps, wrong_order = detect_breaches(planned_steps, as_is_steps)

            # Determine breach type
            if missing_steps and wrong_order:
                breach_type = "Boomer"
            elif missing_steps:
                breach_type = "Missing Steps"
            elif wrong_order:
                breach_type = "Steps Out of Order"
            else:
                breach_type = "None"

            # Prepare HTML-formatted details
            details_parts = []
            if missing_steps:
                details_parts.append("<strong>Missing Steps:</strong><ul>" +
                                     ''.join(f"<li>{step}</li>" for step in missing_steps) +
                                     "</ul>")
            if wrong_order:
                details_parts.append("<strong>Out of Order:</strong><ul>" +
                                     ''.join(f"<li>{step}</li>" for step in wrong_order) +
                                     "</ul>")
            if not details_parts:
                details_parts.append("<strong>No Breach</strong>")

            results.append({
                "Order_ID": order_id,
                "Customer_ID": customer_id,
                "Item_ID": item_id,
                "Export_Flag": export_flag,
                "Dangerous_Flag": dangerous_flag,
                "Derived_Scenario": derived_scenario,
                "Scenario_Used": scenario_used,
                "Planned_Steps_Count": len(planned_steps),
                "As_Is_Steps_Count": len(as_is_steps),
                "Missing_Steps_Count": len(missing_steps),
                "Out_of_Order_Steps_Count": len(wrong_order),
                "Case_ID": f"{order_id}_{item_id}",
                "Breach_Type": breach_type,
                "Details": "<br>".join(details_parts)
            })

        # Create chart
        chart_base64 = generate_breach_plot(results)

        # Save to CSV (optional for backend storage)
        if results:
            pd.DataFrame(results).to_csv("breach_results.csv", index=False)

        return jsonify({"results": results, "chart": chart_base64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

