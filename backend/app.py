from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
from backend.utils import detect_breaches, generate_breach_plot

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        filename = file.filename.lower()

        # Support both CSV and Excel formats
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xls', '.xlsx')):
            in_memory_file = io.BytesIO(file.read())
            df = pd.read_excel(in_memory_file)
        else:
            return jsonify({"error": "Unsupported file format. Upload CSV or Excel."}), 400

        # Required columns (Based on test data)
        required_columns = [
            'Order-No.', 'Customer-No.', 'Item-No.',
            'Export to not EU [1 = n, 2 = y]', 'Dangerous Good [1 = n, 2 = y]',
            'Planed-Master-Scenario-No.',
            'Planed-Master-Order-Processing-Ongoing Position No.',
            'Planed-Master-Order-Processing-Position-No. as an ID',
            'Planed-Master-Order-Processing-Start-Time',
            'Planed-Master-Order-Processing-End-Time',
            'As-Is-Real-Order-Processing-Ongoing Position No.',
            'As-Is-Master-Order-Processing-Position-No. as an ID',
            'As-Is-Real-Order-Processing-Start-Time',
            'As-Is-Real-Order-Processing-End-Time',
            'Final Yield Quantity',
            'Total Scrap Quantity'
        ]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return jsonify({"error": f"Missing columns: {missing_cols}"}), 400

        results = []
        grouped = df.groupby(['Order-No.', 'Item-No.'])

        for (order_id, item_id), group in grouped:
            planned_steps = list(group.sort_values('Planed-Master-Order-Processing-Ongoing Position No.')[
                'Planed-Master-Order-Processing-Position-No. as an ID'])
            actual_steps = list(group.sort_values('As-Is-Real-Order-Processing-Ongoing Position No.')[
                'As-Is-Master-Order-Processing-Position-No. as an ID'])

            missing_steps, out_of_order_steps = detect_breaches(planned_steps, actual_steps)

            planned_start = pd.to_datetime(group['Planed-Master-Order-Processing-Start-Time']).min()
            planned_end = pd.to_datetime(group['Planed-Master-Order-Processing-End-Time']).max()
            planned_duration = (planned_end - planned_start).total_seconds() / 60 if pd.notna(planned_start) and pd.notna(planned_end) else None

            actual_start = pd.to_datetime(group['As-Is-Real-Order-Processing-Start-Time']).min()
            actual_end = pd.to_datetime(group['As-Is-Real-Order-Processing-End-Time']).max()
            actual_duration = (actual_end - actual_start).total_seconds() / 60 if pd.notna(actual_start) and pd.notna(actual_end) else None

            time_deviation = actual_duration - planned_duration if planned_duration is not None and actual_duration is not None else None

            total_yield = group['Final Yield Quantity'].sum()
            total_scrap = group['Total Scrap Quantity'].sum()

            if missing_steps and out_of_order_steps:
                breach_type = "Both"
            elif missing_steps:
                breach_type = "Missing"
            elif out_of_order_steps:
                breach_type = "Out of Order"
            else:
                breach_type = "None"

            details_parts = []
            if missing_steps:
                details_parts.append("<strong>Missing Steps:</strong><ul>" + ''.join(f"<li>{s}</li>" for s in missing_steps) + "</ul>")
            if out_of_order_steps:
                details_parts.append("<strong>Out of Order:</strong><ul>" + ''.join(f"<li>{s}</li>" for s in out_of_order_steps) + "</ul>")
            if not details_parts:
                details_parts.append("<strong>No Breach</strong>")

            results.append({
                "Order_ID": order_id,
                "Customer_ID": group['Customer-No.'].iloc[0],
                "Item_ID": item_id,
                "Export_Flag": group['Export to not EU [1 = n, 2 = y]'].iloc[0],
                "Dangerous_Flag": group['Dangerous Good [1 = n, 2 = y]'].iloc[0],
                "Derived_Scenario": group['Planed-Master-Scenario-No.'].iloc[0],
                "Scenario_Used": group['Planed-Master-Scenario-No.'].iloc[0],
                "Planned_Steps_Count": len(planned_steps),
                "As_Is_Steps_Count": len(actual_steps),
                "Time_Planned_Minutes": planned_duration,
                "Time_Actual_Minutes": actual_duration,
                "Time_Deviation_Minutes": time_deviation,
                "Missing_Steps_Count": len(missing_steps),
                "Out_of_Order_Steps_Count": len(out_of_order_steps),
                "Missing_Steps": missing_steps,
                "Out_of_Order_Steps": out_of_order_steps,
                "Case_ID": f"{order_id}_{item_id}",
                "Breach_Type": breach_type,
                "Details": "<br>".join(details_parts),
                "Total_Yield": total_yield,
                "Total_Scrap": total_scrap
            })

        df_results = pd.DataFrame(results)

        if not df_results.empty:
            scenario_summary = df_results.groupby('Derived_Scenario').agg({
                'Missing_Steps_Count': 'mean',
                'Out_of_Order_Steps_Count': 'mean',
                'Time_Deviation_Minutes': 'mean',
                'Order_ID': 'count',
                'Breach_Type': lambda x: x.mode()[0] if not x.mode().empty else 'None',
                'Total_Yield': 'sum',
                'Total_Scrap': 'sum'
            }).rename(columns={
                'Order_ID': 'Num_Orders',
                'Missing_Steps_Count': 'Avg_Missing_Steps',
                'Out_of_Order_Steps_Count': 'Avg_Out_of_Order_Steps',
                'Time_Deviation_Minutes': 'Avg_Time_Deviation_Minutes',
                'Breach_Type': 'Most_Common_Breach_Type',
                'Total_Yield': 'Sum_Total_Yield',
                'Total_Scrap': 'Sum_Total_Scrap'
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
