let breachResults = [];

const analyzeBtn = document.getElementById('analyzeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const csvFileInput = document.getElementById('csvFile');
const statusMessage = document.getElementById('statusMessage');
const spinner = document.getElementById('spinner');

analyzeBtn.addEventListener('click', handleAnalyzeAndDashboard);
downloadBtn.addEventListener('click', downloadCSV);

function formatNumber(value) {
    if (value === null || value === undefined || isNaN(value)) return '';
    return Number(value).toFixed(2);
}

async function handleAnalyzeAndDashboard() {
    const file = csvFileInput.files[0];
    if (!file) {
        alert("Please select a CSV file!");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    statusMessage.textContent = "Analyzing... Please wait.";
    statusMessage.className = "";
    spinner.style.display = "block";
    analyzeBtn.disabled = true;

    try {
        const response = await fetch('https://process-mining-ui.onrender.com/analyze-with-dashboard', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }

        const data = await response.json();
        breachResults = data.results || [];

        // Fill tables
        renderAllTables();
        if (data.scenario_summary) renderScenarioSummary(data.scenario_summary);

        // Main breach chart
        if (data.chart) {
            const breachChart = document.getElementById('breachChart');
            if (breachChart) {
                breachChart.src = data.chart;
                breachChart.style.display = "block";
            }
        }

        // Dashboard charts
        if (data.dashboard) {
            document.getElementById('chartScenarioSummary').src = data.dashboard.scenario_summary;
            document.getElementById('chartBreachCounts').src = data.dashboard.breach_counts;
            document.getElementById('chartBreachTypeDist').src = data.dashboard.breach_type_dist;
            document.getElementById('chartImpact').src = data.dashboard.impact_chart;
            document.getElementById('chartScenarioBreachType').src = data.dashboard.scenario_breach_type;
            document.getElementById('chartTimeDevDist').src = data.dashboard.time_dev_dist;
        }

        statusMessage.className = "success";
        statusMessage.textContent = "Analysis and dashboard loaded successfully!";
    } catch (error) {
        statusMessage.className = "error";
        statusMessage.textContent = `Error: ${error.message}`;
        alert(`Error: ${error.message}`);
    } finally {
        spinner.style.display = "none";
        analyzeBtn.disabled = false;
    }
}

function renderAllTables() {
    const basicBody = document.querySelector('#basicTable tbody');
    const timingBody = document.querySelector('#timingTable tbody');
    const breachBody = document.querySelector('#breachTable tbody');
    const quantityBody = document.querySelector('#quantityTable tbody');

    basicBody.innerHTML = timingBody.innerHTML = breachBody.innerHTML = quantityBody.innerHTML = "";

    breachResults.forEach(breach => {
        // Basic Info
        basicBody.innerHTML += `
        <tr>
            <td>${breach.Order_ID}</td>
            <td>${breach.Item_ID}</td>
            <td>${breach.Customer_ID}</td>
            <td>${breach.Export_Flag}</td>
            <td>${breach.Dangerous_Flag}</td>
            <td>${breach.Derived_Scenario}</td>
            <td>${breach.Scenario_Used}</td>
            <td>${breach.Case_ID}</td>
        </tr>`;

        // Timing Info
        timingBody.innerHTML += `
        <tr>
            <td>${breach.Order_ID}</td>
            <td>${breach.Item_ID}</td>
            <td>${breach.Planned_Start || ''}</td>
            <td>${breach.Planned_End || ''}</td>
            <td>${breach.Actual_Start || ''}</td>
            <td>${breach.Actual_End || ''}</td>
            <td>${formatNumber(breach.Time_Planned_Minutes)}</td>
            <td>${formatNumber(breach.Time_Actual_Minutes)}</td>
            <td>${formatNumber(breach.Time_Deviation_Minutes)}</td>
        </tr>`;

        // Breach Details
        breachBody.innerHTML += `
        <tr>
            <td>${breach.Order_ID}</td>
            <td>${breach.Item_ID}</td>
            <td>${breach.Planned_Steps_Count}</td>
            <td>${breach.As_Is_Steps_Count}</td>
            <td>${breach.Breach_Type}</td>
            <td>${breach.Missing_Steps_Count}</td>
            <td>${breach.Out_of_Order_Steps_Count}</td>
            <td>${breach.Details}</td>
        </tr>`;

        // Production Quantities
        quantityBody.innerHTML += `
        <tr>
            <td>${breach.Order_ID}</td>
            <td>${breach.Item_ID}</td>
            <td>${breach.Total_Yield}</td>
            <td>${breach.Total_Scrap}</td>
            <td>${formatNumber(breach.Quantity_Deviation_Percent)}</td>
        </tr>`;
    });
}

function renderScenarioSummary(summary) {
    const summaryTableBody = document.querySelector('#scenarioSummaryTable tbody');
    summaryTableBody.innerHTML = '';
    summary.forEach(row => {
        summaryTableBody.innerHTML += `
        <tr>
            <td>${row.Derived_Scenario || row.Scenario}</td>
            <td>${row.Num_Orders}</td>
            <td>${row.Most_Common_Breach_Type}</td>
            <td>${formatNumber(row.Avg_Missing_Steps)}</td>
            <td>${formatNumber(row.Avg_Out_of_Order_Steps)}</td>
        </tr>`;
    });
}

function downloadCSV() {
    if (!breachResults.length) {
        alert("No data to download!");
        return;
    }

    const header = [
        "Order ID", "Item ID", "Customer ID", "Export Flag", "Dangerous Flag",
        "Derived Scenario", "Scenario Used", "Planned Steps Count", "As-Is Steps Count",
        "Planned Start", "Planned End", "Actual Start", "Actual End",
        "Time Planned Minutes", "Time Actual Minutes", "Time Deviation Minutes",
        "Case ID", "Breach Type", "Details", "Final Yield Quantity",
        "Total Scrap Quantity", "Quantity Deviation Percent"
    ];

    const rows = breachResults.map(breach => [
        breach.Order_ID, breach.Item_ID, breach.Customer_ID, breach.Export_Flag, breach.Dangerous_Flag,
        breach.Derived_Scenario, breach.Scenario_Used, breach.Planned_Steps_Count, breach.As_Is_Steps_Count,
        breach.Planned_Start || '', breach.Planned_End || '', breach.Actual_Start || '', breach.Actual_End || '',
        formatNumber(breach.Time_Planned_Minutes), formatNumber(breach.Time_Actual_Minutes), formatNumber(breach.Time_Deviation_Minutes),
        breach.Case_ID, breach.Breach_Type, breach.Details, breach.Total_Yield, breach.Total_Scrap,
        formatNumber(breach.Quantity_Deviation_Percent)
    ]);

    let csvContent = header.join(",") + "\n";
    rows.forEach(r => {
        csvContent += r.map(val => `"${val}"`).join(",") + "\n";
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
