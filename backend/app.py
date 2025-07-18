from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from backend.utils import get_expected_steps, detect_breaches, generate_breach_plot
import random
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

        required_columns = {"Order ID", "Customer ID", "Item ID",
                           "Export Flag", "Dangerous Flag", "Planned Steps", "As Is Steps"}
        if not required_columns.issubset(df.columns):
            return jsonify({"error": f"CSV much include columns: {','.join(required_columns)}"}), 400
        
        results = []

        for _, row in df.iterrows():
            order_id = row['Order ID']
            customer_id = row['Customer ID']
            item_id = row['Item ID']
            export_flag = int(row['Export Flag'])
            dangerous_flag = int(row['Dangerous Flag'])                                
            expected_steps = get_expected_steps(export_flag, dangerous_flag)

            planned_steps = row['Planned Steps'].split('|')
            as_is_steps = row['As Is Steps'].split('|')

            
            missing_steps, wrong_order = detect_breaches(expected_steps, as_is_steps)

            if missing_steps or wrong_order:
                results.append({
                    "Order_ID": order_id,
                    "Customer_ID": customer_id,
                    "Item_ID": item_id,
                    "Missing steps": missing_steps,
                    "Out of Order Steps": wrong_order,
                    "Breach_Type": "Boomer" if missing_steps or wrong_order else "None",
                    "Details": f"Missing: {', '.join(missing_steps)} | Order Issue: {', '.join(wrong_order)}"
                })

        
        chart_base64 = generate_breach_plot(results)
        if results:
             pd.DataFrame(results).to_csv("breach_results.csv", index=False)    
        return jsonify({"results": results, "chart": chart_base64})
    except Exception as e:
            return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=10000)

