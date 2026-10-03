// Visual Timetable Management: Full College Timetable, Multi-dimensional Filters, Drag & Drop Editing, Export & Print

let currentTimetable = [];
let currentViewMode = 'weekly'; // 'weekly' | 'compact' | 'daily'
let activeDay = 'Monday';
const WORKING_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

document.addEventListener('DOMContentLoaded', () => {
    loadTimetableData();

    // Filters
    document.getElementById('filterBatch')?.addEventListener('change', () => loadTimetableData());
    document.getElementById('filterFaculty')?.addEventListener('change', () => loadTimetableData());
    document.getElementById('filterRoom')?.addEventListener('change', () => loadTimetableData());
    document.getElementById('filterDept')?.addEventListener('change', () => loadTimetableData());

    // View Toggles
    const weeklyBtn = document.getElementById('viewModeWeekly');
    const compactBtn = document.getElementById('viewModeCompact');
    const dailyBtn = document.getElementById('viewModeDaily');

    function setActiveBtn(activeBtn) {
        [weeklyBtn, compactBtn, dailyBtn].forEach(b => {
            if (b) {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-outline-primary');
            }
        });
        if (activeBtn) {
            activeBtn.classList.remove('btn-outline-primary');
            activeBtn.classList.add('btn-primary', 'active');
        }
    }

    if (weeklyBtn) {
        weeklyBtn.addEventListener('click', () => {
            currentViewMode = 'weekly';
            setActiveBtn(weeklyBtn);
            renderCalendar();
        });
    }

    if (compactBtn) {
        compactBtn.addEventListener('click', () => {
            currentViewMode = 'compact';
            setActiveBtn(compactBtn);
            renderCalendar();
        });
    }

    if (dailyBtn) {
        dailyBtn.addEventListener('click', () => {
            currentViewMode = 'daily';
            setActiveBtn(dailyBtn);
            renderCalendar();
        });
    }

    // CSV Export
    document.getElementById('exportTimetableCsvBtn')?.addEventListener('click', () => {
        exportCsv();
    });

    // Print
    document.getElementById('printTimetableBtn')?.addEventListener('click', () => {
        window.print();
    });
});

async function loadTimetableData() {
    const tbody = document.getElementById('timetableGridBody');
    const countBadge = document.getElementById('scheduleCountBadge');
    const titleEl = document.getElementById('currentScheduleTitle');

    const batchSelect = document.getElementById('filterBatch');
    const batchId = batchSelect?.value || '';
    const facultyId = document.getElementById('filterFaculty')?.value || '';
    const roomId = document.getElementById('filterRoom')?.value || '';
    const dept = document.getElementById('filterDept')?.value || '';

    const params = new URLSearchParams();
    if (batchId) params.append('batch_id', batchId);
    if (facultyId) params.append('faculty_id', facultyId);
    if (roomId) params.append('classroom_id', roomId);
    if (dept) params.append('department', dept);

    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-5 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading full college academic calendar schedule...
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`/api/timetable?${params.toString()}`);
        const json = await res.json();
        currentTimetable = json.data || [];

        if (countBadge) countBadge.innerText = `${currentTimetable.length} sessions`;

        if (batchId && batchSelect) {
            const bText = batchSelect.selectedOptions[0]?.text || 'Student Batch';
            if (titleEl) titleEl.innerText = `Batch Schedule: ${bText}`;
        } else if (facultyId) {
            const fText = document.getElementById('filterFaculty').selectedOptions[0]?.text;
            if (titleEl) titleEl.innerText = `Faculty Schedule: ${fText}`;
        } else if (roomId) {
            const rText = document.getElementById('filterRoom').selectedOptions[0]?.text;
            if (titleEl) titleEl.innerText = `Classroom Schedule: ${rText}`;
        } else {
            if (titleEl) titleEl.innerText = `Global Campus Timetable (All Batches)`;
        }

        renderCalendar();

    } catch (err) {
        console.error('Error loading timetable:', err);
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Error loading timetable.</td></tr>';
    }
}

function renderCalendar() {
    const tbody = document.getElementById('timetableGridBody');
    if (!tbody) return;

    const isDaily = currentViewMode === 'daily';
    const isCompact = currentViewMode === 'compact';
    const daysToRender = isDaily ? [activeDay] : WORKING_DAYS;

    // Index sessions by day_period
    const sessionMap = {};
    currentTimetable.forEach(s => {
        const key = `${s.day}_${s.period}`;
        if (!sessionMap[key]) sessionMap[key] = [];
        sessionMap[key].push(s);
    });

    let html = '';

    daysToRender.forEach(day => {
        html += `<tr>`;
        html += `<td class="td-day-header">${day}</td>`;

        // Periods 1 to 4
        for (let p = 1; p <= 4; p++) {
            const key = `${day}_${p}`;
            const sessions = sessionMap[key] || [];
            html += `
                <td class="timetable-cell ${isCompact ? 'compact-cell' : ''}" data-day="${day}" data-period="${p}"
                    ondragover="handleDragOver(event)"
                    ondragleave="handleDragLeave(event)"
                    ondrop="handleDrop(event, '${day}', ${p})">
                    ${renderCellSessions(sessions, isCompact)}
                </td>
            `;
        }

        // Lunch Recess Column (Between Period 4 and Period 5)
        html += `<td class="recess-column"><span>LUNCH RECESS</span></td>`;

        // Periods 5 to 6
        for (let p = 5; p <= 6; p++) {
            const key = `${day}_${p}`;
            const sessions = sessionMap[key] || [];
            html += `
                <td class="timetable-cell ${isCompact ? 'compact-cell' : ''}" data-day="${day}" data-period="${p}"
                    ondragover="handleDragOver(event)"
                    ondragleave="handleDragLeave(event)"
                    ondrop="handleDrop(event, '${day}', ${p})">
                    ${renderCellSessions(sessions, isCompact)}
                </td>
            `;
        }

        html += `</tr>`;
    });

    tbody.innerHTML = html;
}

function renderCellSessions(sessions, isCompact = false) {
    if (sessions.length === 0) {
        return `<span class="text-muted d-block text-center py-3" style="opacity: 0.3;">&mdash;</span>`;
    }

    if (isCompact) {
        return sessions.map(s => {
            const isLab = s.subject_type === 'Lab';
            const color = s.color_hex || (isLab ? '#19B6B1' : '#315EAA');

            return `
                <div class="session-compact-pill"
                     style="border-left: 3px solid ${color}; background-color: ${hexToRgba(color, 0.08)}; padding: 3px 6px; margin-bottom: 3px; border-radius: 4px; font-size: 0.72rem; cursor: pointer;"
                     onclick="openSessionDetails(${s.id})"
                     title="${s.subject_name} &bull; ${s.batch_name} &bull; ${s.faculty_name} &bull; ${s.classroom_name}">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong style="color: ${color};">${s.subject_code}</strong>
                        <span class="text-muted" style="font-size: 0.65rem;">${s.classroom_name}</span>
                    </div>
                    <div class="text-truncate text-muted" style="font-size: 0.68rem;">${s.batch_name}</div>
                </div>
            `;
        }).join('');
    }

    return sessions.map(s => {
        const isLab = s.subject_type === 'Lab';
        const color = s.color_hex || (isLab ? '#19B6B1' : '#315EAA');

        return `
            <div class="session-card-saas"
                 style="border-left-color: ${color}; background-color: ${hexToRgba(color, 0.07)};"
                 draggable="true"
                 data-session-id="${s.id}"
                 ondragstart="handleDragStart(event, ${s.id})"
                 onclick="openSessionDetails(${s.id})">
                <div class="session-top-meta">
                    <span class="session-code-badge" style="color: ${color}; font-weight: 700;">${s.subject_code}</span>
                    <span class="session-room-pill"><i class="fa-solid fa-door-open me-1"></i>${s.classroom_name}</span>
                </div>
                <span class="session-subject-name" title="${s.subject_name}">${s.subject_name}</span>
                <div class="session-instructor-line">
                    <i class="fa-solid fa-chalkboard-user"></i>
                    <span>${s.faculty_name}</span>
                </div>
                <div class="session-batch-line d-flex justify-content-between align-items-center mt-1">
                    <span class="badge bg-light text-dark border" style="font-size: 0.65rem;">${s.batch_name}</span>
                    ${isLab ? '<span class="badge bg-info-subtle text-info border border-info" style="font-size: 0.6rem;">Lab</span>' : ''}
                </div>
            </div>
        `;
    }).join('');
}

// --------------------------------------------------------------------------
// Drag and Drop Timetable Editing with Live Constraint Validation
// --------------------------------------------------------------------------
let draggedSessionId = null;

function handleDragStart(e, sessionId) {
    draggedSessionId = sessionId;
    e.dataTransfer.setData('text/plain', sessionId);
    e.target.classList.add('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    const cell = e.currentTarget;
    cell.classList.add('drag-over');
}

function handleDragLeave(e) {
    const cell = e.currentTarget;
    cell.classList.remove('drag-over');
}

async function handleDrop(e, targetDay, targetPeriod) {
    e.preventDefault();
    const cell = e.currentTarget;
    cell.classList.remove('drag-over');

    document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));

    if (!draggedSessionId) return;

    try {
        const response = await fetch('/api/timetable/move', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                timetable_id: draggedSessionId,
                target_day: targetDay,
                target_period: targetPeriod
            })
        });

        const json = await response.json();

        if (response.ok && json.status === 'success') {
            showToast(`Session successfully moved to ${targetDay} Period ${targetPeriod}!`);
            loadTimetableData();
        } else {
            const errMsg = json.message || "Conflict: Cannot move session into this slot.";
            showToast(errMsg, true);
        }
    } catch (err) {
        console.error('Drag drop error:', err);
        showToast("Error updating session location", true);
    } finally {
        draggedSessionId = null;
    }
}

// Helper: Hex to RGBA
function hexToRgba(hex, alpha) {
    let c = hex.replace('#', '');
    if (c.length === 3) c = c[0] + c[0] + c[1] + c[1] + c[2] + c[2];
    const num = parseInt(c, 16);
    return `rgba(${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}, ${alpha})`;
}

function openSessionDetails(sessionId) {
    const s = currentTimetable.find(item => item.id === sessionId);
    if (!s) return;

    const modalBody = document.getElementById('classDetailModalBody');
    modalBody.innerHTML = `
        <div class="row g-3">
            <div class="col-12 d-flex justify-content-between align-items-center pb-2 border-bottom">
                <span class="badge-saas badge-saas-primary fs-6">${s.session_code}</span>
                <span class="badge-saas ${s.subject_type === 'Lab' ? 'badge-saas-accent' : 'badge-saas-secondary'}">
                    ${s.subject_type} Course
                </span>
            </div>
            <div class="col-12">
                <h4 class="fw-bold mb-1" style="color: var(--primary);">${s.subject_name}</h4>
                <small class="text-muted">Code: ${s.subject_code} &bull; Batch: ${s.batch_name}</small>
            </div>
            <div class="col-6">
                <label class="form-label-saas text-muted">Faculty Instructor</label>
                <strong><i class="fa-solid fa-chalkboard-user text-primary me-1"></i>${s.faculty_name}</strong>
            </div>
            <div class="col-6">
                <label class="form-label-saas text-muted">Classroom / Lab</label>
                <strong><i class="fa-solid fa-door-open text-accent me-1"></i>${s.classroom_name} (Cap: ${s.classroom_capacity})</strong>
            </div>
            <div class="col-6">
                <label class="form-label-saas text-muted">Time Window</label>
                <strong>${s.day} Period ${s.period} (${s.start_time} - ${s.end_time})</strong>
            </div>
            <div class="col-6">
                <label class="form-label-saas text-muted">Student Cohort</label>
                <strong>${s.batch_name} (${s.student_strength} students)</strong>
            </div>
            <div class="col-12 pt-2 border-top">
                <small class="text-muted">Algorithm used: <span class="badge-saas badge-saas-secondary">${s.algorithm_used || 'DAA Hybrid'}</span></small>
            </div>
        </div>
    `;

    new bootstrap.Modal(document.getElementById('classDetailModal')).show();
}

function exportCsv() {
    window.location.href = '/api/reports/export-csv/timetable';
}

function showToast(message, isError = false) {
    let toast = document.getElementById('liveToastEl');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'liveToastEl';
        toast.style.position = 'fixed';
        toast.style.bottom = '24px';
        toast.style.right = '24px';
        toast.style.zIndex = '9999';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '8px';
        toast.style.fontSize = '14px';
        toast.style.fontWeight = '500';
        toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
        toast.style.transition = 'all 0.3s ease';
        document.body.appendChild(toast);
    }
    toast.style.background = isError ? '#EF4444' : '#10B981';
    toast.style.color = '#FFFFFF';
    toast.innerText = message;
    toast.style.display = 'block';
    toast.style.opacity = '1';

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => { toast.style.display = 'none'; }, 300);
    }, 3500);
}
