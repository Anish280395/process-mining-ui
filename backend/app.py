from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io, base64
import matplotlib.pyplot as plt
from backend.utils import detect_breaches, generate_breach_plot, calculate_quantity_deviation, CORPORATE_COLORS, SCENARIO_STEPS

app = Flask(__name__)
CORS(app)

def safe_duration(start, end):
    try:
        if pd.isna(start) or pd.isna(end):
            return None
        duration = (end - start).total_seconds() / 60
        return duration if duration >= 0 else None
    except Exception:
        return None

def convert_types(obj):
    if isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif hasattr(obj, 'item'):
        return obj.item()
    else:
        return obj

def fig_to_base64(fig):
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", facecolor="white")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

def style_ax(ax, title, xlabel=None, ylabel=None):
    ax.set_title(title, fontsize=14, color="#2d3748", fontweight="bold")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12, color="#2d3748")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12, color="#2d3748")
    ax.grid(axis="y", linestyle="--", alpha=0.6)

def most_common_breach(series):
    filtered = series[series != 'None']
    if filtered.empty:
        return 'None'
    return filtered.mode().iloc[0]

@app.route('/analyze-with-dashboard', methods=['POST'])
def analyze_with_dashboard():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        filename = file.filename.lower()

        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xls', '.xlsx')):
            in_memory_file = io.BytesIO(file.read())
            df = pd.read_excel(in_memory_file)
        else:
            return jsonify({"error": "Unsupported file format. Upload CSV or Excel."}), 400

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

        # Parse dates
        date_cols = [
            'Planed-Master-Order-Processing-Start-Time',
            'Planed-Master-Order-Processing-End-Time',
            'As-Is-Real-Order-Processing-Start-Time',
            'As-Is-Real-Order-Processing-End-Time'
        ]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        results = []
        grouped = df.groupby(['Order-No.', 'Item-No.'])
        for (order_id, item_id), group in grouped:
            scenario = group['Planed-Master-Scenario-No.'].iloc[0]
            planned_steps = SCENARIO_STEPS.get(scenario, [])  # <- Always use reference!
            actual_steps = list(group.sort_values('As-Is-Real-Order-Processing-Ongoing Position No.')[
                'As-Is-Master-Order-Processing-Position-No. as an ID'])

            missing_steps, out_of_order_steps, extra_steps, duplicates = detect_breaches(planned_steps, actual_steps)

            planned_start = group['Planed-Master-Order-Processing-Start-Time'].min()
            planned_end = group['Planed-Master-Order-Processing-End-Time'].max()
            actual_start = group['As-Is-Real-Order-Processing-Start-Time'].min()
            actual_end = group['As-Is-Real-Order-Processing-End-Time'].max()

            planned_duration = safe_duration(planned_start, planned_end)
            actual_duration = safe_duration(actual_start, actual_end)
            time_deviation = (actual_duration - planned_duration) if (planned_duration is not None and actual_duration is not None) else None

            total_yield = group['Final Yield Quantity'].fillna(0).sum()
            total_scrap = group['Total Scrap Quantity'].fillna(0).sum()

            # Breach type logic
            breach_type = "None"
            if missing_steps and out_of_order_steps:
                breach_type = "Both"
            elif missing_steps:
                breach_type = "Missing"
            elif out_of_order_steps:
                breach_type = "Out of Order"
            if extra_steps or duplicates:
                if breach_type == "None":
                    breach_type = "Extra/Duplicates"
                else:
                    breach_type += " + Extra/Duplicates"

            # Details
            details_parts = []
            if missing_steps:
                details_parts.append("<strong>Missing Steps:</strong><ul>" +
                                    ''.join(f"<li>{s}</li>" for s in missing_steps) + "</ul>")
            if out_of_order_steps:
                details_parts.append("<strong>Out of Order:</strong><ul>" +
                                    ''.join(f"<li>{s}</li>" for s in out_of_order_steps) + "</ul>")
            if extra_steps:
                details_parts.append("<strong>Extra Steps (unexpected):</strong><ul>" +
                                    ''.join(f"<li>{s}</li>" for s in extra_steps) + "</ul>")
            if duplicates:
                details_parts.append("<strong>Duplicate Steps:</strong><ul>" +
                                    ''.join(f"<li>{s}</li>" for s in duplicates) + "</ul>")
            if not details_parts:
                details_parts.append("<strong>No Breach</strong>")
            details_parts.append(f"<strong>Counts:</strong> Missing - {len(missing_steps)} | Out-of-Order - {len(out_of_order_steps)} | Extra - {len(extra_steps)} | Duplicates - {len(duplicates)}")

            results.append({
                "Order_ID": order_id,
                "Customer_ID": group['Customer-No.'].iloc[0],
                "Item_ID": item_id,
                "Export_Flag": group['Export to not EU [1 = n, 2 = y]'].iloc[0],
                "Dangerous_Flag": group['Dangerous Good [1 = n, 2 = y]'].iloc[0],
                "Derived_Scenario": scenario,
                "Scenario_Used": scenario,
                "Planned_Steps_Count": len(planned_steps),
                "As_Is_Steps_Count": len(actual_steps),
                "Planned_Start": planned_start.strftime("%Y-%m-%d %H:%M") if pd.notna(planned_start) else None,
                "Planned_End": planned_end.strftime("%Y-%m-%d %H:%M") if pd.notna(planned_end) else None,
                "Actual_Start": actual_start.strftime("%Y-%m-%d %H:%M") if pd.notna(actual_start) else None,
                "Actual_End": actual_end.strftime("%Y-%m-%d %H:%M") if pd.notna(actual_end) else None,
                "Time_Planned_Minutes": planned_duration,
                "Time_Actual_Minutes": actual_duration,
                "Time_Deviation_Minutes": time_deviation,
                "Missing_Steps_Count": len(missing_steps),
                "Out_of_Order_Steps_Count": len(out_of_order_steps),
                "Extra_Steps_Count": len(extra_steps),
                "Duplicate_Steps_Count": len(duplicates),
                "Missing_Steps": missing_steps,
                "Out_of_Order_Steps": out_of_order_steps,
                "Extra_Steps": extra_steps,
                "Duplicates": duplicates,
                "Case_ID": f"{order_id}_{item_id}",
                "Breach_Type": breach_type,
                "Details": "<br>".join(details_parts),
                "Total_Yield": total_yield,
                "Total_Scrap": total_scrap,
                "Quantity_Deviation_Percent": calculate_quantity_deviation(total_yield, total_scrap),
            })

        safe_results = convert_types(results)
        df_results = pd.DataFrame(safe_results)

        scenario_summary_json = []
        if not df_results.empty:
            scenario_summary = df_results.groupby('Derived_Scenario').agg({
                'Missing_Steps_Count': 'mean',
                'Out_of_Order_Steps_Count': 'mean',
                'Time_Deviation_Minutes': 'mean',
                'Order_ID': 'count',
                'Breach_Type': most_common_breach,
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
            scenario_summary_json = convert_types(scenario_summary.to_dict(orient='records'))

        chart_base64 = generate_breach_plot(results)

        # Dashboard charts (no change needed)
        charts = {}
        # ... [charts code remains unchanged, as in your existing app.py] ...

        # Chart 1
        fig1, ax1 = plt.subplots()
        scenario_counts = df['Planed-Master-Scenario-No.'].value_counts()
        scenario_counts.plot(kind='bar', color=CORPORATE_COLORS["blue"], ax=ax1)
        style_ax(ax1, "Scenario Summary", ylabel="Number of Orders")
        charts["scenario_summary"] = fig_to_base64(fig1)

        # Chart 2
        breach_counts = pd.Series([r['Breach_Type'] != 'None' for r in safe_results]).value_counts()
        fig2, ax2 = plt.subplots()
        breach_counts.plot(kind='bar', color=[CORPORATE_COLORS["green"], CORPORATE_COLORS["red"]], ax=ax2)
        style_ax(ax2, "Breach vs No Breach", ylabel="Number of Orders")
        ax2.set_xticklabels(['No Breach', 'Breach'], rotation=0)
        charts["breach_counts"] = fig_to_base64(fig2)

        # Chart 3
        breach_type_counts = pd.Series([r['Breach_Type'] for r in safe_results]).value_counts()
        fig3, ax3 = plt.subplots()
        breach_type_counts.plot(kind='pie', autopct='%1.1f%%', colors=[
            CORPORATE_COLORS["red"], CORPORATE_COLORS["orange"], CORPORATE_COLORS["yellow"], CORPORATE_COLORS["green"]
        ], ax=ax3)
        ax3.set_ylabel("")
        style_ax(ax3, "Breach Type Distribution")
        charts["breach_type_dist"] = fig_to_base64(fig3)

        # Chart 4
        time_dev = [r['Time_Deviation_Minutes'] for r in safe_results if r['Time_Deviation_Minutes'] is not None]
        qty_dev = [r['Quantity_Deviation_Percent'] for r in safe_results]
        fig4, ax4 = plt.subplots()
        ax4.scatter(time_dev, qty_dev, c=CORPORATE_COLORS["blue"])
        style_ax(ax4, "Impact on Time & Yield", "Time Deviation (minutes)", "Quantity Deviation (%)")
        charts["impact_chart"] = fig_to_base64(fig4)

        # Chart 5
        scen_breach_df = df_results.groupby(['Derived_Scenario', 'Breach_Type']).size().unstack(fill_value=0)
        fig5, ax5 = plt.subplots()
        scen_breach_df.plot(kind='bar', stacked=True, ax=ax5, color=[
            CORPORATE_COLORS["green"], CORPORATE_COLORS["red"], CORPORATE_COLORS["orange"], CORPORATE_COLORS["yellow"]
        ])
        style_ax(ax5, "Scenario vs Breach Type", ylabel="Number of Orders")
        charts["scenario_breach_type"] = fig_to_base64(fig5)

        # Chart 6
        fig6, ax6 = plt.subplots()
        ax6.hist(time_dev, bins=15, color=CORPORATE_COLORS["blue"], edgecolor="white")
        style_ax(ax6, "Time Deviation Distribution", "Minutes", "Frequency")
        charts["time_dev_dist"] = fig_to_base64(fig6)

        return jsonify({
            "results": safe_results,
            "scenario_summary": scenario_summary_json,
            "chart": chart_base64,
            "dashboard": charts
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
