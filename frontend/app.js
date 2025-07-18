let breachResults = [];

const analyzeBtn = document.getElementById('analyzeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const csvFileInput = document.getElementById('csvFile');
const breachTableBody = document.querySelector('#breachTable tbody');
const statusMessage = document.getElementById('statusMessage');
const spinner = document.getElementById('spinner');
const breachTable = document.getElementById('breachTable');
const breachChart = document.getElementById('breachChart');

// Event Listeners

analyzeBtn.addEventListener('click', handleAnalyze);
downloadBtn.addEventListener('click', downloadCSV);

//function

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
        //  Adjust this URL for local testing
        const response = await fetch('https://anish-validator-api.onrender.com/analyze', {
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

        // Show chart if available
        const chartImage = document.getElementById('breachChart');
        if (data.chart) {
            chartImage.src = data.chart;
            chartImage.style.display = "block";
        } else {
            chartImage.style.display = "none";
        }

        statusMessage.className = "success";
        statusMessage.textContent = "Analysis completed successfully!";
        spinner.style.display = "none"
        // Handle of chart!
        if (data.chart) {

            breachChart.src = data.chart;
            breachChart.style.display = "block";
        } else {
            breachChart.style.display = "none";
        }

        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Process";
    } catch (error) {
        spinner.style.display = "none";
        breachChart.style.display = "none";
        statusMessage.className = "error";
        statusMessage.textContext = `Error: ${error.message}`;
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Process";
        alert(`Error: ${error.message}`);
    }
}

function renderResults() {
    breachTableBody.innerHTML = '';

    if (breachResults.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 5;
        cell.textContent = 'No breaches detected';
        row.appendChild(cell);
        breachTableBody.appendChild(row);
        return;
    }

    breachResults.forEach(breach => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${breach["Order_ID"]}</td>
            <td>${breach["Customer_ID"]}</td>
            <td>${breach["Item_ID"]}</td>
            <td>${breach["Breach_Type"]}</td>
            <td>${breach["Details"]}</td>
        `;
        breachTableBody.appendChild(row);
    });
}

function downloadCSV() {
    if (breachResults.length === 0) {
        alert("No breaches to download!");
        return;
    }

    const header = ["Case ID", "Breach Type", "Details"];
    const rows = breachResults.map(breach => [
        breach["Case ID"],
        breach["Breach Type"],
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