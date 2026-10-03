// Timetable Generator Client: Algorithm Execution, Metrics, & Step Trace

let currentExecutionResult = null;

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generateTimetableForm');
    const regenBtn = document.getElementById('regenerateBtn');
    const viewTraceBtn = document.getElementById('viewTraceBtn');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            runGeneration();
        });
    }

    if (regenBtn) {
        regenBtn.addEventListener('click', () => {
            runGeneration();
        });
    }

    if (viewTraceBtn) {
        viewTraceBtn.addEventListener('click', () => {
            showTraceModal();
        });
    }
});

async function runGeneration() {
    const submitBtn = document.getElementById('generateSubmitBtn');
    const idleBox = document.getElementById('solverIdleState');
    const loadingBox = document.getElementById('solverLoadingState');
    const metricsBox = document.getElementById('solverMetricsState');
    const statusBadge = document.getElementById('solverStatusBadge');

    const algorithm = document.querySelector('input[name="algorithm"]:checked')?.value || 'graph_coloring';
    const batchVal = document.getElementById('batchSelect')?.value;
    const batch_ids = (batchVal === 'all' || !batchVal) ? null : [parseInt(batchVal)];

    const working_days = Array.from(document.querySelectorAll('input[name="working_days"]:checked')).map(cb => cb.value);
    if (working_days.length === 0) {
        alert('Please select at least one working day.');
        return;
    }

    const periods_per_day = parseInt(document.getElementById('periodsInput')?.value) || 6;

    // Set UI to loading state
    idleBox.classList.add('d-none');
    metricsBox.classList.add('d-none');
    loadingBox.classList.remove('d-none');
    statusBadge.innerText = 'Executing Solver...';
    statusBadge.className = 'badge-saas badge-saas-warning';
    if (submitBtn) submitBtn.disabled = true;

    try {
        const response = await fetch('/api/generate-timetable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                algorithm,
                batch_ids,
                working_days,
                periods_per_day
            })
        });

        const json = await response.json();

        loadingBox.classList.add('d-none');
        metricsBox.classList.remove('d-none');
        if (submitBtn) submitBtn.disabled = false;

        if (json.status !== 'success' || !json.result) {
            statusBadge.innerText = 'Failed';
            statusBadge.className = 'badge-saas badge-saas-danger';
            document.getElementById('resultBanner').className = 'alert alert-danger d-flex align-items-center mb-4';
            document.getElementById('resultBannerTitle').innerText = 'Generation Unsuccessful';
            document.getElementById('resultBannerSubtitle').innerText = json.message || 'Constraints could not be satisfied.';
            return;
        }

        const res = json.result;
        currentExecutionResult = res;

        // Populate KPI numbers
        document.getElementById('resExecTime').innerText = `${res.execution_time_ms} ms`;
        document.getElementById('resScheduled').innerText = `${res.scheduled_classes} / ${res.total_classes}`;
        document.getElementById('resConflicts').innerText = res.conflicts_count ?? 0;
        document.getElementById('resBacktracks').innerText = `${res.backtracking_steps} backtracks`;
        document.getElementById('resDecisions').innerText = `${res.decisions_count} decisions`;

        const banner = document.getElementById('resultBanner');
        const title = document.getElementById('resultBannerTitle');
        const subtitle = document.getElementById('resultBannerSubtitle');

        if (res.success && res.conflicts_count === 0 && res.unscheduled_classes === 0) {
            statusBadge.innerText = '100% Conflict-Free';
            statusBadge.className = 'badge-saas badge-saas-success';
            banner.className = 'alert alert-success d-flex align-items-center mb-4';
            title.innerText = `Timetable Generated Successfully (${res.algorithm})!`;
            subtitle.innerText = `Scheduled all ${res.scheduled_classes} classes across batches with zero constraint violations.`;
            showToast(`Timetable generated using ${res.algorithm}!`);
        } else {
            statusBadge.innerText = 'Partial / Tight Constraints';
            statusBadge.className = 'badge-saas badge-saas-warning';
            banner.className = 'alert alert-warning d-flex align-items-center mb-4';
            title.innerText = `Partial Schedule Generated (${res.algorithm})`;
            subtitle.innerText = `Scheduled ${res.scheduled_classes}/${res.total_classes} classes. ${res.unscheduled_classes} could not be placed due to tight constraints.`;
            showToast(`Generated partial timetable with ${res.scheduled_classes} sessions.`, true);
        }

    } catch (err) {
        console.error('Generation error:', err);
        loadingBox.classList.add('d-none');
        idleBox.classList.remove('d-none');
        if (submitBtn) submitBtn.disabled = false;
        showToast("Error communicating with scheduling engine", true);
    }
}

function showTraceModal() {
    if (!currentExecutionResult) return;

    const tbody = document.getElementById('traceTableBody');
    const trace = currentExecutionResult.step_trace || [];

    if (trace.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No step trace recorded for this run.</td></tr>';
    } else {
        tbody.innerHTML = trace.map((t, i) => `
            <tr>
                <td><strong>#${t.step || (i + 1)}</strong></td>
                <td><strong class="text-primary">${t.session_code || '-'}</strong></td>
                <td>${t.subject || '-'}</td>
                <td><span class="badge-saas badge-saas-primary">${t.batch || '-'}</span></td>
                <td>${t.faculty || '-'}</td>
                <td><span class="session-room-pill">${t.room || '-'}</span></td>
                <td><strong>${t.day || ''}</strong> ${t.period ? `P${t.period}` : ''}</td>
                <td>
                    <span class="badge-saas ${t.status === 'Assigned' ? 'badge-saas-success' : 'badge-saas-danger'}">
                        ${t.status === 'Assigned' ? '<i class="fa-solid fa-check me-1"></i> Valid' : '<i class="fa-solid fa-arrow-rotate-left me-1"></i> Backtracked'}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    new bootstrap.Modal(document.getElementById('traceModal')).show();
}
