from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from backend.utils import detect_breaches, generate_breach_plot

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze_csv():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        df = pd.read_csv(file)

        # Make sure these columns exist (adapt names if needed)
        required_columns = {
            "Order ID", "Customer ID", "Item ID",
            "Export Flag", "Dangerous Flag",
            "Derived Scenario", "Scenario Used",
            "Planned Steps", "As Is Steps"
        }
        if not required_columns.issubset(df.columns):
            return jsonify({"error": f"CSV must include columns: {', '.join(required_columns)}"}), 400

        results = []
        minutes_per_step = 10 # Assuming each step takes 10 minutes

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

            if missing_steps and wrong_order:
                breach_type = "Both"
            elif missing_steps:
                breach_type = "Missing"
            elif wrong_order:
                breach_type = "Out of Order"
            else:
                breach_type = "None"
            planned_steps_count = len(planned_steps)
            as_is_steps_count = len(as_is_steps)

            time_planned = planned_steps_count * minutes_per_step
            time_actual = as_is_steps_count * minutes_per_step
            time_deviation = time_actual - time_planned

            results.append({
                "Order_ID": order_id,
                "Customer_ID": customer_id,
                "Item_ID": item_id,
                "Export_Flag": export_flag,
                "Dangerous_Flag": dangerous_flag,
                "Derived_Scenario": derived_scenario,
                "Scenario_Used": scenario_used,
                "Planned_Steps_Count": planned_steps_count,
                "As_Is_Steps_Count": as_is_steps_count,
                "Time_Planned_Minutes": time_planned,
                "Time_Actual_Minutes": time_actual,
                "Time_Deviation_Minutes": time_deviation,
                "Missing_Steps_Count": len(missing_steps),
                "Out_of_Order_Steps_Count": len(wrong_order),
                "Missing_Steps": missing_steps,
                "Out_of_Order_Steps": wrong_order,
                "Case_ID": f"{order_id}_{item_id}",
                "Breach_Type": breach_type,
                "Details": (
                    (f"<strong>Missing Steps:</strong><ul>{''.join(f'<li>{s}</li>' for s in missing_steps)}</ul>" if missing_steps else "") +
                    (f"<strong>Out of Order:</strong><ul>{''.join(f'<li>{s}</li>' for s in wrong_order)}</ul>" if wrong_order else "") or
                    "<strong>No Breach</strong>"
                )
            })

        # Scenario-level aggregation
        df_results = pd.DataFrame(results)
        if not df_results.empty:
            scenario_summary = df_results.groupby('Derived_Scenario').agg({
                'Missing_Steps_Count': 'mean',
                'Out_of_Order_Steps_Count': 'mean',
                'Time_Deviation_Minutes': 'mean',
                'Order_ID': 'count',
                'Breach_Type': lambda x: x.mode()[0] if not x.mode().empty else 'None'
            }).rename(columns={
                'Order_ID': 'Num_Orders',
                'Missing_Steps_Count': 'Avg_Missing_Steps',
                'Out_of_Order_Steps_Count': 'Avg_Out_of_Order_Steps',
                'Time_Deviation_Minutes': 'Avg_Time_Deviation',
                'Breach_Type': 'Most_Common_Breach_Type'
            }).reset_index()
            scenario_summary_json = scenario_summary.to_dict(orient='records')
        else:
            scenario_summary_json = []

        chart_base64 = generate_breach_plot(results)

        return jsonify({
            "results": results,
            "scenario_summary": scenario_summary_json,
            "chart": chart_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)