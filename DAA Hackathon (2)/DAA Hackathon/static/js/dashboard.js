// Dashboard Client: Stats, Charts, and Recent Schedules

let weeklyOverviewChart = null;
let roomUtilChart = null;
let facultyWorkloadChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard-stats');
        const json = await response.json();
        if (json.status !== 'success' || !json.data) return;

        const data = json.data;

        // 1. KPI Cards
        document.getElementById('kpiSubjects').innerText = data.total_subjects ?? 0;
        document.getElementById('kpiFaculty').innerText = data.total_faculty ?? 0;
        document.getElementById('kpiClassrooms').innerText = data.total_classrooms ?? 0;
        document.getElementById('kpiBatches').innerText = data.total_batches ?? 0;
        document.getElementById('kpiScheduled').innerText = data.scheduled_classes ?? 0;
        document.getElementById('kpiUnscheduled').innerText = data.unscheduled_classes ?? 0;

        // Update notification dot if conflicts
        const dot = document.getElementById('topbarConflictDot');
        if (dot) {
            dot.style.display = data.conflicts_count > 0 ? 'block' : 'none';
        }

        // 2. Charts
        if (data.charts) {
            renderWeeklyOverview(data.charts.weekly_overview);
            renderRoomUtilization(data.charts.room_utilization);
            renderFacultyWorkload(data.charts.faculty_workload);
        }

        // 3. Recent Activities Feed
        renderRecentActivities(data.recent_activities || []);

    } catch (err) {
        console.error('Error fetching dashboard stats:', err);
    }
}

function renderWeeklyOverview(chartData) {
    const ctx = document.getElementById('weeklyOverviewChart');
    if (!ctx || !chartData) return;

    if (weeklyOverviewChart) weeklyOverviewChart.destroy();

    weeklyOverviewChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Scheduled Classes',
                data: chartData.counts,
                backgroundColor: 'rgba(49, 94, 170, 0.75)',
                borderColor: '#315EAA',
                borderWidth: 1.5,
                borderRadius: 6,
                maxBarThickness: 42
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#17243A',
                    titleColor: '#FFFFFF',
                    bodyColor: '#B5C4D8',
                    padding: 10
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#64748B' } },
                y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { color: '#64748B', stepSize: 2 } }
            }
        }
    });
}

function renderRoomUtilization(chartData) {
    const ctx = document.getElementById('roomUtilChart');
    if (!ctx || !chartData) return;

    if (roomUtilChart) roomUtilChart.destroy();

    roomUtilChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Utilization %',
                data: chartData.utilization_pct,
                backgroundColor: 'rgba(25, 182, 177, 0.75)',
                borderColor: '#19B6B1',
                borderWidth: 1.5,
                borderRadius: 6,
                maxBarThickness: 28
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Utilization: ${ctx.raw}% of weekly capacity`
                    }
                }
            },
            scales: {
                x: { max: 100, grid: { color: '#F1F5F9' }, ticks: { color: '#64748B' } },
                y: { grid: { display: false }, ticks: { color: '#263449', font: { weight: 500 } } }
            }
        }
    });
}

function renderFacultyWorkload(chartData) {
    const ctx = document.getElementById('facultyWorkloadChart');
    if (!ctx || !chartData) return;

    if (facultyWorkloadChart) facultyWorkloadChart.destroy();

    facultyWorkloadChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Scheduled Hours',
                    data: chartData.scheduled,
                    backgroundColor: 'rgba(32, 164, 119, 0.75)',
                    borderColor: '#20A477',
                    borderWidth: 1.5,
                    borderRadius: 6,
                    maxBarThickness: 24
                },
                {
                    label: 'Weekly Limit',
                    data: chartData.max_hours,
                    backgroundColor: 'rgba(226, 232, 240, 0.85)',
                    borderColor: '#CBD5E1',
                    borderWidth: 1.5,
                    borderRadius: 6,
                    maxBarThickness: 24
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { color: '#64748B', font: { size: 11 } } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#64748B' } },
                y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { color: '#64748B' } }
            }
        }
    });
}

function renderRecentActivities(classes) {
    const tbody = document.getElementById('recentActivitiesTableBody');
    if (!tbody) return;

    if (classes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    No classes scheduled yet. <a href="/generate" class="text-primary fw-semibold">Generate a timetable</a> to begin.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = classes.map(c => `
        <tr>
            <td><strong class="session-code-badge">${c.session_code}</strong></td>
            <td><strong>${c.subject_name}</strong> <small class="text-muted">(${c.subject_code})</small></td>
            <td><span class="badge-saas badge-saas-primary">${c.batch_name}</span></td>
            <td><i class="fa-solid fa-chalkboard-user text-muted me-1"></i> ${c.faculty_name}</td>
            <td><span class="session-room-pill">${c.classroom_name}</span></td>
            <td><strong>${c.day}</strong> &bull; Period ${c.period}</td>
            <td><span class="badge-saas badge-saas-secondary">${c.algorithm_used || 'DAA'}</span></td>
        </tr>
    `).join('');
}
