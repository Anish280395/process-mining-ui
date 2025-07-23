let breachResults = [];

const analyzeBtn = document.getElementById('analyzeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const csvFileInput = document.getElementById('csvFile');
const breachTableBody = document.querySelector('#breachTable tbody');
const statusMessage = document.getElementById('statusMessage');
const spinner = document.getElementById('spinner');
const breachChart = document.getElementById('breachChart');
const breachTable = document.getElementById('breachTable');

analyzeBtn.addEventListener('click', handleAnalyze);
downloadBtn.addEventListener('click', downloadCSV);

async function handleAnalyze() {
    const file = csvFileInput.files[0];
    if (!file) {
        alert("Please select a CSV file!");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    statusMessage.className = "";
    statusMessage.textContent = "Analyzing... Please wait.";
    spinner.style.display = "block";
    breachChart.style.display = "none";

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";

    try {
        const response = await fetch('https://process-mining-ui.onrender.com/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }

        const data = await response.json();
        breachResults = data.results;
        renderResults();
        if (data.scenario_summary) {
            renderScenarioSummary(data.scenario_summary);
        }
        if (data.chart) {
            breachChart.src = data.chart;
            breachChart.style.display = "block";
        } else {
            breachChart.style.display = "none";
        }

        statusMessage.className = "success";
        statusMessage.textContent = "Analysis completed successfully!";
    } catch (error) {
        spinner.style.display = "none";
        breachChart.style.display = "none";
        statusMessage.className = "error";
        statusMessage.textContent = `Error: ${error.message}`;
        alert(`Error: ${error.message}`);
    } finally {
        spinner.style.display = "none";
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Process";
    }
}

function renderResults() {
    breachTableBody.innerHTML = '';

    if (breachResults.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 17;  // updated colspan for new columns
        cell.textContent = 'No breaches detected';
        row.appendChild(cell);
        breachTableBody.appendChild(row);
        return;
    }

    breachResults.forEach(breach => {
        const row = document.createElement('tr');

        const detailsHtml = `
            ${breach["Details"] || "<em>No Breach</em>"}
            <br>
            <strong>Counts:</strong>
            Missing - ${breach["Missing_Steps_Count"]}&nbsp;&nbsp;|&nbsp;&nbsp;
            Out-of-Order - ${breach["Out_of_Order_Steps_Count"]}
        `;

        row.innerHTML = `
          <td>${breach["Order_ID"]}</td>
          <td>${breach["Customer_ID"]}</td>
          <td>${breach["Item_ID"]}</td>
          <td>${breach["Export_Flag"]}</td>
          <td>${breach["Dangerous_Flag"]}</td>
          <td>${breach["Derived_Scenario"]}</td>
          <td>${breach["Scenario_Used"]}</td>
          <td>${breach["Planned_Steps_Count"]}</td>
          <td>${breach["As_Is_Steps_Count"]}</td>
          <td>${breach["Time_Planned_Minutes"]}</td>
          <td>${breach["Time_Actual_Minutes"]}</td>
          <td>${breach["Time_Deviation_Minutes"]}</td>
          <td>${breach["Missing_Steps_Count"]}</td>
          <td>${breach["Out_of_Order_Steps_Count"]}</td>
          <td>${breach["Case_ID"]}</td>
          <td>${breach["Breach_Type"]}</td>
          <td>${detailsHtml}</td>
        `;
        breachTableBody.appendChild(row);
    });
}

function downloadCSV() {
    if (breachResults.length === 0) {
        alert("No breaches to download!");
        return;
    }

    const header = [
        "Order ID", "Customer ID", "Item ID", "Export Flag", "Dangerous Flag",
        "Derived Scenario", "Scenario Used", "Planned Steps Count", "As-Is Steps Count",
        "Time Planned Minutes", "Time Actual Minutes", "Time Deviation Minutes",
        "Missing Steps Count", "Out of Order Steps Count", "Case ID", "Breach Type", "Details"
    ];

    const rows = breachResults.map(breach => [
        breach["Order_ID"],
        breach["Customer_ID"],
        breach["Item_ID"],
        breach["Export_Flag"],
        breach["Dangerous_Flag"],
        breach["Derived_Scenario"],
        breach["Scenario_Used"],
        breach["Planned_Steps_Count"],
        breach["As_Is_Steps_Count"],
        breach["Time_Planned_Minutes"],
        breach["Time_Actual_Minutes"],
        breach["Time_Deviation_Minutes"],
        breach["Missing_Steps_Count"],
        breach["Out_of_Order_Steps_Count"],
        breach["Case_ID"],
        breach["Breach_Type"],
        breach["Details"]
    ]);

    let csvContent = header.join(",") + "\n";
    rows.forEach(r => {
        csvContent += r.join(",") + "\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'breach_report.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function renderScenarioSummary(summary) {
    const summaryTableBody = document.querySelector('#scenarioSummaryTable tbody');
    if (!summaryTableBody) return; // avoid errors if no table in DOM
    summaryTableBody.innerHTML = '';

    summary.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.Derived_Scenario || row.Scenario}</td>
            <td>${row.Num_Orders}</td>
            <td>${row.Most_Common_Breach_Type}</td>
            <td>${row.Avg_Missing_Steps.toFixed(2)}</td>
            <td>${row.Avg_Out_of_Order_Steps.toFixed(2)}</td>
        `;
        summaryTableBody.appendChild(tr);
    });
}
