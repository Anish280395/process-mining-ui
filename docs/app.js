let breachResults = [];

const analyzeBtn = document.getElementById('analyzeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const csvFileInput = document.getElementById('csvFile');
const statusMessage = document.getElementById('statusMessage');
const spinner = document.getElementById('spinner');

analyzeBtn.addEventListener('click', handleAnalyze);
downloadBtn.addEventListener('click', downloadCSV);

function formatNumber(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '';
    }
    return Number(value).toFixed(2);
}

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

        renderAllTables();

        if (data.scenario_summary) {
            renderScenarioSummary(data.scenario_summary);
        }

        statusMessage.className = "success";
        statusMessage.textContent = "Analysis completed successfully!";
    } catch (error) {
        statusMessage.className = "error";
        statusMessage.textContent = `Error: ${error.message}`;
        alert(`Error: ${error.message}`);
    } finally {
        spinner.style.display = "none";
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Process";
    }
}

function renderAllTables() {
    const basicBody = document.querySelector('#basicTable tbody');
    const timingBody = document.querySelector('#timingTable tbody');
    const breachBody = document.querySelector('#breachTable tbody');
    const quantityBody = document.querySelector('#quantityTable tbody');

    basicBody.innerHTML = "";
    timingBody.innerHTML = "";
    breachBody.innerHTML = "";
    quantityBody.innerHTML = "";

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

        // Production Quantity
        const totalQty = breach.Total_Yield + breach.Total_Scrap;
        const qtyDeviation = totalQty > 0 ? (breach.Total_Scrap / totalQty * 100).toFixed(2) : "0.00";

        quantityBody.innerHTML += `
        <tr>
            <td>${breach.Order_ID}</td>
            <td>${breach.Item_ID}</td>
            <td>${breach.Total_Yield}</td>
            <td>${breach.Total_Scrap}</td>
            <td>${qtyDeviation}</td>
        </tr>`;
    });
}

function renderScenarioSummary(summary) {
    const summaryTableBody = document.querySelector('#scenarioSummaryTable tbody');
    summaryTableBody.innerHTML = '';

    summary.forEach(row => {
        const avgMissing = (typeof row.Avg_Missing_Steps === 'number') ? row.Avg_Missing_Steps.toFixed(2) : '';
        const avgOutOfOrder = (typeof row.Avg_Out_of_Order_Steps === 'number') ? row.Avg_Out_of_Order_Steps.toFixed(2) : '';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.Derived_Scenario || row.Scenario}</td>
            <td>${row.Num_Orders}</td>
            <td>${row.Most_Common_Breach_Type}</td>
            <td>${avgMissing}</td>
            <td>${avgOutOfOrder}</td>
        `;
        summaryTableBody.appendChild(tr);
    });
}

function downloadCSV() {
    if (breachResults.length === 0) {
        alert("No data to download!");
        return;
    }

    const header = [
        "Order ID", "Item ID", "Customer ID", "Export Flag", "Dangerous Flag",
        "Derived Scenario", "Scenario Used", "Planned Steps Count", "As-Is Steps Count",
        "Planned Start", "Planned End", "Actual Start", "Actual End",
        "Time Planned Minutes", "Time Actual Minutes", "Time Deviation Minutes",
        "Case ID", "Breach Type", "Details", "Final Yield Quantity", "Total Scrap Quantity"
    ];

    const rows = breachResults.map(breach => [
        breach.Order_ID,
        breach.Item_ID,
        breach.Customer_ID,
        breach.Export_Flag,
        breach.Dangerous_Flag,
        breach.Derived_Scenario,
        breach.Scenario_Used,
        breach.Planned_Steps_Count,
        breach.As_Is_Steps_Count,
        breach.Planned_Start || '',
        breach.Planned_End || '',
        breach.Actual_Start || '',
        breach.Actual_End || '',
        formatNumber(breach.Time_Planned_Minutes),
        formatNumber(breach.Time_Actual_Minutes),
        formatNumber(breach.Time_Deviation_Minutes),
        breach.Case_ID,
        breach.Breach_Type,
        breach.Details,
        breach.Total_Yield,
        breach.Total_Scrap
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
