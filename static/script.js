let chartCostComparison = null;
let chartShortagesAvoided = null;
let chartCostBreakdown = null;
let allRecommendations = [];

// Load Dashboard Data & Render Charts
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();
        
        // Populate Summary Cards directly from canonical validation experiment summary
        document.getElementById('stat-components').innerText = data.summary.total_components;
        document.getElementById('stat-locations').innerText = data.summary.total_locations;
        document.getElementById('stat-shortages').innerText = data.summary.active_shortages;
        document.getElementById('stat-transfers').innerText = data.summary.transfer_recommendations;
        document.getElementById('stat-purchase-avoided').innerText = '₹' + data.summary.purchase_avoided.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('stat-shortages-avoided').innerText = data.summary.shortages_avoided + ' cases';
        
        document.getElementById('shortage-count-badge').innerText = `${data.summary.active_shortages} Shortage Cases Detected`;
        
        // Render Warnings if present
        const warnContainer = document.getElementById('warnings-container');
        if (data.warnings && data.warnings.length > 0) {
            warnContainer.innerHTML = data.warnings.map(w => `
                <div class="card callout-box" style="border-left-color: var(--accent-red); margin-bottom: 1rem;">
                    <strong>${w.type}:</strong> ${w.message} (${w.dataset})
                </div>
            `).join('');
        } else {
            warnContainer.innerHTML = '';
        }

        // Render Shortage Table
        renderShortageTable(data.shortages);

        // Render ONLY 3 Charts using canonical validation cost & case numbers
        renderChart1CostComparison(data.summary.baseline_purchase, data.summary.recommender_purchase);
        renderChart2ShortagesAvoided(data.summary.shortages_avoided, data.summary.purchase_recommendations);
        renderChart3CostBreakdown(data.summary.recommender_transfer, data.summary.recommender_purchase);

    } catch (err) {
        console.error("Error loading dashboard data:", err);
    }
}

// Chart 1: Baseline Purchase Cost vs Recommender Purchase Cost
function renderChart1CostComparison(baseline, recommender) {
    const ctx = document.getElementById('chartCostComparison').getContext('2d');
    if (chartCostComparison) chartCostComparison.destroy();

    chartCostComparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Baseline Purchase Cost', 'Recommender Purchase Cost'],
            datasets: [{
                label: 'Cost (₹ INR)',
                data: [baseline, recommender],
                backgroundColor: ['rgba(244, 63, 94, 0.7)', 'rgba(52, 211, 153, 0.7)'],
                borderColor: ['#f43f5e', '#34d399'],
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(val) { return '₹' + val.toLocaleString('en-IN'); }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Chart 2: Shortage Cases Avoided via Transfers vs Purchase Fallbacks
function renderChart2ShortagesAvoided(avoidedCases, purchaseFallbacks) {
    const ctx = document.getElementById('chartShortagesAvoided').getContext('2d');
    if (chartShortagesAvoided) chartShortagesAvoided.destroy();

    chartShortagesAvoided = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Shortage Cases Resolved via Transfer', 'Supplier Purchase Fallbacks Required'],
            datasets: [{
                data: [avoidedCases, purchaseFallbacks],
                backgroundColor: ['#38bdf8', '#fbbf24'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', boxWidth: 12, padding: 15 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + ' cases';
                        }
                    }
                }
            }
        }
    });
}

// Chart 3: Transfer Freight Cost vs Supplier Purchase Cost
function renderChart3CostBreakdown(transferCost, purchaseCost) {
    const ctx = document.getElementById('chartCostBreakdown').getContext('2d');
    if (chartCostBreakdown) chartCostBreakdown.destroy();

    chartCostBreakdown = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Inter-Location Freight Cost', 'Direct Supplier Purchase Cost'],
            datasets: [{
                label: 'Cost (₹ INR)',
                data: [transferCost, purchaseCost],
                backgroundColor: ['rgba(56, 189, 248, 0.7)', 'rgba(192, 132, 252, 0.7)'],
                borderColor: ['#38bdf8', '#c084fc'],
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(val) { return '₹' + val.toLocaleString('en-IN'); }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function renderShortageTable(shortages) {
    const tbody = document.getElementById('shortage-table-body');
    if (!shortages || shortages.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No active shortages detected.</td></tr>';
        return;
    }

    tbody.innerHTML = shortages.map(s => `
        <tr>
            <td><strong>${s.component_id}</strong> - ${s.component_name}</td>
            <td>${s.location}</td>
            <td>${s.current_stock}</td>
            <td>${s.forecast_7_days}</td>
            <td style="color: var(--accent-red); font-weight: 600;">${s.projected_stock}</td>
            <td><span class="badge badge-danger">${s.shortage} units</span></td>
            <td><span class="badge ${s.urgency === 'CRITICAL' ? 'badge-danger' : s.urgency === 'HIGH' ? 'badge-warning' : 'badge-primary'}">${s.urgency}</span></td>
            <td><span class="badge ${s.confidence === 'HIGH' ? 'badge-success' : s.confidence === 'MEDIUM' ? 'badge-info' : 'badge-warning'}">${s.confidence}</span></td>
        </tr>
    `).join('');
}

// Load Recommendations List Data
async function loadRecommendationsData() {
    try {
        const response = await fetch('/api/recommendations');
        allRecommendations = await response.json();
        
        document.getElementById('rec-count-badge').innerText = `${allRecommendations.length} Recommendations`;
        renderRecommendationsTable(allRecommendations);
    } catch (err) {
        console.error("Error loading recommendations:", err);
    }
}

function renderRecommendationsTable(recs) {
    const tbody = document.getElementById('recommendation-table-body');
    if (!recs || recs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="text-center">No recommendations match filter criteria.</td></tr>';
        return;
    }

    tbody.innerHTML = recs.map(r => {
        const statusBadge = r.status === 'APPROVED' ? 'badge-success' :
                            r.status === 'REJECTED' ? 'badge-danger' :
                            r.status === 'OVERRIDDEN' ? 'badge-warning' : 'badge-primary';
                            
        return `
            <tr style="cursor: pointer;" onclick="window.location.href='/recommendation/${r.recommendation_id}'">
                <td><strong>${r.recommendation_id}</strong></td>
                <td>${r.component_id} (${r.component_name})</td>
                <td><strong>${r.source}</strong> → <strong>${r.destination}</strong></td>
                <td>${r.recommended_quantity} units</td>
                <td>${r.num_packs} packs (${r.pack_size}/pack)</td>
                <td>${r.transfer_time_days} days</td>
                <td>₹${r.transfer_cost.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td>${r.decision_score > 0 ? r.decision_score : 'N/A'}</td>
                <td><span class="badge ${r.confidence === 'HIGH' ? 'badge-success' : r.confidence === 'MEDIUM' ? 'badge-info' : 'badge-warning'}">${r.confidence}</span></td>
                <td><span class="badge ${statusBadge}">${r.status}</span></td>
                <td>
                    <a href="/recommendation/${r.recommendation_id}" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="event.stopPropagation();">Details →</a>
                </td>
            </tr>
        `;
    }).join('');
}

function filterRecommendations(filterType, element) {
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (element) element.classList.add('active');

    if (filterType === 'ALL') {
        renderRecommendationsTable(allRecommendations);
    } else if (filterType === 'TRANSFER' || filterType === 'PURCHASE') {
        renderRecommendationsTable(allRecommendations.filter(r => r.type === filterType));
    } else if (filterType === 'PENDING_APPROVAL') {
        renderRecommendationsTable(allRecommendations.filter(r => r.status === 'PENDING_APPROVAL'));
    }
}

// Load Single Recommendation Details
async function loadSingleRecommendationDetails(recId) {
    const container = document.getElementById('details-container');
    try {
        const response = await fetch(`/api/recommendation/${recId}`);
        if (!response.ok) {
            container.innerHTML = '<div class="card text-center p-xl"><h3>Recommendation Not Found</h3></div>';
            return;
        }
        
        const r = await response.json();
        
        const statusBadge = r.status === 'APPROVED' ? 'badge-success' :
                            r.status === 'REJECTED' ? 'badge-danger' :
                            r.status === 'OVERRIDDEN' ? 'badge-warning' : 'badge-primary';

        container.innerHTML = `
            <div class="detail-header-grid">
                <!-- Primary Information -->
                <div class="card">
                    <div class="flex-between" style="margin-bottom: 1rem;">
                        <h2>Recommendation: ${r.recommendation_id}</h2>
                        <span class="badge ${statusBadge}" style="font-size: 0.9rem; padding: 0.4rem 0.8rem;">${r.status}</span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
                        <div>
                            <span class="metric-label">Component</span>
                            <p style="font-size: 1.1rem; font-weight: 600;">${r.component_id} - ${r.component_name}</p>
                        </div>
                        <div>
                            <span class="metric-label">Action Recommended</span>
                            <p style="font-size: 1.1rem; font-weight: 600; color: var(--accent-blue);">${r.type} (${r.source} → ${r.destination})</p>
                        </div>
                        <div>
                            <span class="metric-label">Required Shortage</span>
                            <p style="font-size: 1.1rem; font-weight: 600;">${r.required_quantity} units</p>
                        </div>
                        <div>
                            <span class="metric-label">Recommended Transfer</span>
                            <p style="font-size: 1.1rem; font-weight: 600; color: var(--accent-green);">${r.recommended_quantity} units (${r.num_packs} packs)</p>
                        </div>
                    </div>

                    <!-- Variable Pack-Size Callout -->
                    <div class="callout-box">
                        <strong>📦 Variable Pack-Size Adjustment:</strong>
                        <p style="margin-top: 0.25rem;">${r.pack_adjustment_note}</p>
                    </div>

                    <!-- WHY THIS RECOMMENDATION? Evidence Section -->
                    <div style="margin-top: 1.5rem;">
                        <h4 style="color: var(--accent-blue);">WHY THIS RECOMMENDATION?</h4>
                        <ul class="evidence-list">
                            ${r.evidence.map(e => `<li><span style="color: var(--accent-green);">✓</span> ${e}</li>`).join('')}
                        </ul>
                    </div>
                </div>

                <!-- Metrics & Action Sidebar -->
                <div class="card flex-column" style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h4 style="margin-bottom: 1rem;">Financial & Decision Metrics</h4>
                        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                            <div class="flex-between">
                                <span class="metric-label">Transfer Freight Cost:</span>
                                <strong>₹${r.transfer_cost.toLocaleString('en-IN', {minimumFractionDigits: 2})}</strong>
                            </div>
                            <div class="flex-between">
                                <span class="metric-label">Supplier Purchase Cost:</span>
                                <strong>₹${r.purchase_cost.toLocaleString('en-IN', {minimumFractionDigits: 2})}</strong>
                            </div>
                            <div class="flex-between">
                                <span class="metric-label">Cost Savings:</span>
                                <strong style="color: var(--accent-green);">₹${r.cost_difference.toLocaleString('en-IN', {minimumFractionDigits: 2})}</strong>
                            </div>
                            <div class="flex-between">
                                <span class="metric-label">Decision-Support Score:</span>
                                <strong style="color: var(--accent-purple);">${r.decision_score > 0 ? r.decision_score : 'N/A'}</strong>
                            </div>
                            <div class="flex-between">
                                <span class="metric-label">Lead Time:</span>
                                <strong>${r.transfer_time_days} Days</strong>
                            </div>
                        </div>

                        <hr style="border-color: var(--border-color); margin: 1.25rem 0;">

                        <h4>Uncertainty Communication</h4>
                        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                            Forecast: <strong>${r.uncertainty.forecast} units</strong> (Range: <strong>${r.uncertainty.range_min} - ${r.uncertainty.range_max}</strong>)
                        </p>
                        <p style="margin-top: 0.5rem;">
                            Confidence Rating: <span class="badge ${r.confidence === 'HIGH' ? 'badge-success' : r.confidence === 'MEDIUM' ? 'badge-info' : 'badge-warning'}">${r.confidence}</span>
                        </p>
                        <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 0.5rem; font-style: italic;">
                            "${r.uncertainty.disclaimer}"
                        </p>
                    </div>

                    <!-- Human Approval Buttons -->
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <span class="metric-label" style="display: block; margin-bottom: 0.5rem;">Human Approval Action:</span>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-success" style="flex: 1;" onclick="handleApprove('${r.recommendation_id}')">Approve</button>
                            <button class="btn btn-danger" style="flex: 1;" onclick="handleReject('${r.recommendation_id}')">Reject</button>
                            <button class="btn btn-warning" style="flex: 1;" onclick="openOverrideModal()">Override</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Rejected Sources Section -->
            ${r.rejected_sources && r.rejected_sources.length > 0 ? `
                <div class="card table-card">
                    <div class="card-header">
                        <h4 style="color: var(--accent-red);">Rejected Candidate Transfer Sources (${r.rejected_sources.length})</h4>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Candidate Source</th>
                                <th>Rejection Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${r.rejected_sources.map(rs => `
                                <tr>
                                    <td><strong>${rs.source}</strong></td>
                                    <td style="color: var(--text-muted);">${rs.reason}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : ''}
        `;
    } catch (err) {
        console.error("Error loading recommendation details:", err);
    }
}

// Approval Actions
async function handleApprove(recId) {
    if (!confirm(`Approve recommendation ${recId}?`)) return;
    try {
        const response = await fetch(`/api/recommendation/${recId}/approve`, { method: 'POST' });
        const res = await response.json();
        alert(res.message);
        loadSingleRecommendationDetails(recId);
    } catch (err) {
        console.error(err);
    }
}

async function handleReject(recId) {
    if (!confirm(`Reject recommendation ${recId}?`)) return;
    try {
        const response = await fetch(`/api/recommendation/${recId}/reject`, { method: 'POST' });
        const res = await response.json();
        alert(res.message);
        loadSingleRecommendationDetails(recId);
    } catch (err) {
        console.error(err);
    }
}

function openOverrideModal() {
    document.getElementById('override-modal').classList.remove('hidden');
}

function closeOverrideModal() {
    document.getElementById('override-modal').classList.add('hidden');
}

async function submitOverrideReason() {
    const reason = document.getElementById('override-reason-text').value.trim();
    if (!reason) {
        alert("Please enter a reason for overriding this recommendation.");
        return;
    }

    try {
        const response = await fetch(`/api/recommendation/${currentRecId}/override`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        });
        const res = await response.json();
        closeOverrideModal();
        alert(res.message);
        loadSingleRecommendationDetails(currentRecId);
    } catch (err) {
        console.error(err);
    }
}
