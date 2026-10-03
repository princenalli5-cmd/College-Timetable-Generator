// Faculty Substitution Management Client (Edumerge-inspired)

document.addEventListener('DOMContentLoaded', () => {
    loadSubstitutionHistory();

    const findBtn = document.getElementById('findReplacementsBtn');
    if (findBtn) {
        findBtn.addEventListener('click', () => {
            findSubstitutes();
        });
    }

    const directForm = document.getElementById('directSubForm');
    if (directForm) {
        directForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                timetable_id: parseInt(document.getElementById('modalSessionSelect').value),
                substitute_faculty_id: parseInt(document.getElementById('modalSubFacultySelect').value),
                reason: document.getElementById('modalSubReason').value.trim() || 'Faculty leave'
            };

            try {
                const res = await fetch('/api/substitutions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const json = await res.json();
                if (res.ok) {
                    bootstrap.Modal.getInstance(document.getElementById('requestSubModal')).hide();
                    directForm.reset();
                    showToast("Faculty substitution logged and timetable updated!");
                    loadSubstitutionHistory();
                } else {
                    showToast(json.message || "Failed to log substitution", true);
                }
            } catch (err) {
                console.error(err);
            }
        });
    }
});

async function findSubstitutes() {
    const sessionSelect = document.getElementById('subSessionSelect');
    const sessionId = sessionSelect?.value;
    const container = document.getElementById('recommendationsContainer');
    const tbody = document.getElementById('recommendationsTableBody');

    if (!sessionId) {
        alert('Please select an active scheduled class session first.');
        return;
    }

    container.classList.remove('d-none');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Analyzing faculty availability, domain expertise, and workload headroom...</td></tr>';

    try {
        const res = await fetch(`/api/substitution/recommendations?timetable_id=${sessionId}`);
        const json = await res.json();

        if (json.status !== 'success' || !json.recommendations) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Failed to calculate recommendations.</td></tr>';
            return;
        }

        const recs = json.recommendations;
        if (recs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No candidate faculty members found.</td></tr>';
            return;
        }

        tbody.innerHTML = recs.map(r => {
            const isEligible = r.is_eligible;
            const scoreColor = r.match_score >= 70 ? 'bg-success' : r.match_score >= 40 ? 'bg-warning' : 'bg-danger';

            return `
                <tr>
                    <td><strong>${r.faculty_name}</strong></td>
                    <td><span class="text-muted">${r.department}</span></td>
                    <td><span class="badge-saas badge-saas-secondary">${r.designation}</span></td>
                    <td><strong>${r.current_hours}</strong> / ${r.max_hours} hrs</td>
                    <td style="min-width: 140px;">
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress flex-grow-1" style="height: 6px;">
                                <div class="progress-bar ${scoreColor}" style="width: ${r.match_score}%"></div>
                            </div>
                            <span class="small fw-bold">${r.match_score}%</span>
                        </div>
                        <small class="text-muted" style="font-size: 0.68rem;">${r.reasons.join(' &bull; ')}</small>
                    </td>
                    <td>
                        <span class="badge-saas ${isEligible ? 'badge-saas-success' : 'badge-saas-danger'}">
                            ${isEligible ? '<i class="fa-solid fa-check"></i> Free & Available' : '<i class="fa-solid fa-ban"></i> Conflict / Busy'}
                        </span>
                    </td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-primary-custom"
                                ${!isEligible ? 'disabled' : ''}
                                onclick="applySubstitution(${sessionId}, ${r.faculty_id}, '${r.faculty_name.replace(/'/g, "\\'")}')">
                            <i class="fa-solid fa-check me-1"></i> Assign Substitute
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Error retrieving recommendations.</td></tr>';
    }
}

async function applySubstitution(timetableId, facultyId, facultyName) {
    if (!confirm(`Confirm assigning ${facultyName} as substitute instructor for this session?`)) return;

    try {
        const res = await fetch('/api/substitutions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                timetable_id: timetableId,
                substitute_faculty_id: facultyId,
                reason: 'Intelligent AI recommendation substitute assignment'
            })
        });

        const json = await res.json();
        if (res.ok) {
            showToast(`Substitution applied! ${facultyName} has been assigned to this class.`);
            document.getElementById('recommendationsContainer').classList.add('d-none');
            loadSubstitutionHistory();
        } else {
            showToast(json.message || "Failed to apply substitution", true);
        }
    } catch (err) {
        console.error(err);
    }
}

async function loadSubstitutionHistory() {
    const tbody = document.getElementById('subHistoryTableBody');
    const badge = document.getElementById('subHistoryCountBadge');
    if (!tbody) return;

    try {
        const res = await fetch('/api/substitutions');
        const json = await res.json();
        const list = json.data || [];

        if (badge) badge.innerText = `${list.length} records`;

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No substitution records recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = list.map((s, i) => `
            <tr>
                <td><strong>#${i + 1}</strong></td>
                <td>
                    <strong class="text-primary">${s.subject_name}</strong>
                    <small class="text-muted d-block">${s.session_code} &bull; ${s.batch_name}</small>
                </td>
                <td><span class="text-danger"><i class="fa-solid fa-user-minus me-1"></i>${s.original_faculty_name}</span></td>
                <td><span class="text-success"><i class="fa-solid fa-user-check me-1"></i>${s.substitute_faculty_name}</span></td>
                <td><strong>${s.day}</strong> Period ${s.period}</td>
                <td><span class="text-muted small">${s.reason || 'Leave'}</span></td>
                <td><span class="badge-saas badge-saas-success">${s.status}</span></td>
                <td><small class="text-muted">${s.created_at ? s.created_at.slice(0, 16) : 'Today'}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}
