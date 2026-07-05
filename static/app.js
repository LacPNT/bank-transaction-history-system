const txnForm = document.getElementById('txn-form');
const txnResult = document.getElementById('txn-result');
const monthSelect = document.getElementById('month-select');
const fetchReportBtn = document.getElementById('fetch-report');
const reportOutput = document.getElementById('report-output');

function toIsoTimestamp(datetimeLocalValue) {
  // <input type="datetime-local"> yields "YYYY-MM-DDTHH:MM" (no seconds).
  // Pad to "YYYY-MM-DDTHH:MM:SS" so the backend's datetime.fromisoformat() parses it consistently.
  return datetimeLocalValue.length === 16 ? `${datetimeLocalValue}:00` : datetimeLocalValue;
}

txnForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    transaction_id: document.getElementById('transaction_id').value.trim(),
    transaction_type: document.getElementById('transaction_type').value,
    amount: parseFloat(document.getElementById('amount').value),
    timestamp: toIsoTimestamp(document.getElementById('timestamp').value),
    balance_after: parseFloat(document.getElementById('balance_after').value),
  };

  txnResult.textContent = 'Submitting...';
  txnResult.className = 'result';

  try {
    const response = await fetch('/transaction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (response.ok) {
      txnResult.textContent = data.message || 'Transaction added successfully';
      txnResult.className = 'result ok';
      txnForm.reset();
      await loadReport();
    } else {
      txnResult.textContent = data.error || 'Failed to add transaction';
      txnResult.className = 'result error';
    }
  } catch (err) {
    txnResult.textContent = `Network error: ${err.message}`;
    txnResult.className = 'result error';
  }
});

function renderMonthCard(stats, title) {
  return `
    <div class="stat-grid">
      <div class="stat income">
        <div class="label">${title} — Total Income</div>
        <div class="value">${Number(stats.total_income).toFixed(2)}</div>
      </div>
      <div class="stat expense">
        <div class="label">${title} — Total Expense</div>
        <div class="value">${Number(stats.total_expense).toFixed(2)}</div>
      </div>
      <div class="stat">
        <div class="label">Transaction Count</div>
        <div class="value">${stats.txn_count}</div>
      </div>
      <div class="stat">
        <div class="label">Ending Balance</div>
        <div class="value">${Number(stats.ending_balance).toFixed(2)}</div>
      </div>
    </div>
  `;
}

function renderYearlyTable(data) {
  const rows = Array.from({ length: 12 }, (_, i) => i + 1)
    .map((m) => {
      const s = data[`month_${m}`];
      return `<tr>
        <td>Month ${m}</td>
        <td>${Number(s.total_income).toFixed(2)}</td>
        <td>${Number(s.total_expense).toFixed(2)}</td>
        <td>${s.txn_count}</td>
        <td>${Number(s.ending_balance).toFixed(2)}</td>
      </tr>`;
    })
    .join('');

  return `
    ${renderMonthCard(data.yearly_total, 'Yearly')}
    <table>
      <thead>
        <tr><th>Month</th><th>Income</th><th>Expense</th><th>Txns</th><th>Balance</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

async function loadReport() {
  const month = monthSelect.value;
  reportOutput.innerHTML = '<p class="result">Loading...</p>';

  try {
    const response = await fetch(`/report/${month}`);
    const data = await response.json();

    if (!response.ok) {
      reportOutput.innerHTML = `<p class="result error">${data.error || 'Failed to load report'}</p>`;
      return;
    }

    reportOutput.innerHTML = month === 'all'
      ? renderYearlyTable(data)
      : renderMonthCard(data, `Month ${data.month}`);
  } catch (err) {
    reportOutput.innerHTML = `<p class="result error">Network error: ${err.message}</p>`;
  }
}

fetchReportBtn.addEventListener('click', loadReport);

// Load the yearly summary on first page view.
loadReport();
