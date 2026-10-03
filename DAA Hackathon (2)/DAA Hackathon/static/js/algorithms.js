// DAA Algorithm Analysis, Benchmarking, & Graph Coloring Visualization

let runtimeChart = null;
let efficiencyChart = null;
let currentGraph = null;

document.addEventListener('DOMContentLoaded', () => {
    runBenchmark();

    document.getElementById('runBenchmarkBtn')?.addEventListener('click', () => {
        runBenchmark();
    });

    document.getElementById('reloadGraphBtn')?.addEventListener('click', () => {
        loadGraph();
    });
});

async function runBenchmark() {
    const tableBody = document.getElementById('comparisonTableBody');
    const runBtn = document.getElementById('runBenchmarkBtn');

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Benchmarking...';
    }

    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Executing Graph Coloring, Greedy, Backtracking, and Hybrid algorithms under identical constraints...
            </td>
        </tr>
    `;

    try {
        const response = await fetch('/api/compare-algorithms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const json = await response.json();
        if (json.status !== 'success' || !json.data) return;

        const results = json.data;

        // 1. KPI Cards
        updateKpis(results);

        // 2. Charts
        renderCharts(results);

        // 3. Matrix Table
        renderTable(results);

        // 4. Welsh-Powell Graph Visualizer
        loadGraph();

    } catch (err) {
        console.error('Benchmark error:', err);
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Error running algorithm benchmark suite.</td></tr>';
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run Live Benchmark Suite';
        }
    }
}

function updateKpis(results) {
    const gc = results.graph_coloring;
    const gr = results.greedy;
    const bt = results.backtracking;
    const hb = results.hybrid;

    if (gc) {
        document.getElementById('gcTime').innerText = `${gc.execution_time_ms} ms`;
        document.getElementById('gcScheduled').innerText = `${gc.scheduled_classes} / ${gc.total_classes}`;
        document.getElementById('gcChromatic').innerText = `${gc.chromatic_number || 15} colors`;
    }

    if (gr) {
        document.getElementById('grTime').innerText = `${gr.execution_time_ms} ms`;
        document.getElementById('grScheduled').innerText = `${gr.scheduled_classes} / ${gr.total_classes}`;
        document.getElementById('grUnscheduled').innerText = `${gr.unscheduled_classes} classes`;
    }

    if (bt) {
        document.getElementById('btTime').innerText = `${bt.execution_time_ms} ms`;
        document.getElementById('btScheduled').innerText = `${bt.scheduled_classes} / ${bt.total_classes}`;
        document.getElementById('btBacktracks').innerText = `${bt.backtracking_steps} steps`;
    }

    if (hb) {
        document.getElementById('hbTime').innerText = `${hb.execution_time_ms} ms`;
        document.getElementById('hbScheduled').innerText = `${hb.scheduled_classes} / ${hb.total_classes}`;
    }
}

function renderCharts(results) {
    const labels = ['Graph Coloring', 'Greedy', 'Backtracking', 'Hybrid'];
    const times = [
        results.graph_coloring?.execution_time_ms || 0,
        results.greedy?.execution_time_ms || 0,
        results.backtracking?.execution_time_ms || 0,
        results.hybrid?.execution_time_ms || 0
    ];
    const sched = [
        results.graph_coloring?.scheduled_classes || 0,
        results.greedy?.scheduled_classes || 0,
        results.backtracking?.scheduled_classes || 0,
        results.hybrid?.scheduled_classes || 0
    ];
    const unsched = [
        results.graph_coloring?.unscheduled_classes || 0,
        results.greedy?.unscheduled_classes || 0,
        results.backtracking?.unscheduled_classes || 0,
        results.hybrid?.unscheduled_classes || 0
    ];

    // 1. Runtime Chart
    const rtCtx = document.getElementById('runtimeComparisonChart');
    if (rtCtx) {
        if (runtimeChart) runtimeChart.destroy();
        runtimeChart = new Chart(rtCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Runtime (ms)',
                    data: times,
                    backgroundColor: [
                        'rgba(25, 182, 177, 0.75)',
                        'rgba(32, 164, 119, 0.75)',
                        'rgba(49, 94, 170, 0.75)',
                        'rgba(230, 162, 60, 0.75)'
                    ],
                    borderColor: ['#19B6B1', '#20A477', '#315EAA', '#E6A23C'],
                    borderWidth: 1.5,
                    borderRadius: 6,
                    maxBarThickness: 45
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#64748B' } },
                    y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { color: '#64748B' } }
                }
            }
        });
    }

    // 2. Efficiency Chart
    const effCtx = document.getElementById('efficiencyComparisonChart');
    if (effCtx) {
        if (efficiencyChart) efficiencyChart.destroy();
        efficiencyChart = new Chart(effCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Scheduled Classes',
                        data: sched,
                        backgroundColor: 'rgba(32, 164, 119, 0.8)',
                        borderColor: '#20A477',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        maxBarThickness: 28
                    },
                    {
                        label: 'Unscheduled',
                        data: unsched,
                        backgroundColor: 'rgba(224, 82, 82, 0.8)',
                        borderColor: '#E05252',
                        borderWidth: 1.5,
                        borderRadius: 6,
                        maxBarThickness: 28
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { color: '#64748B' } }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#64748B' } },
                    y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { color: '#64748B' } }
                }
            }
        });
    }
}

function renderTable(results) {
    const tbody = document.getElementById('comparisonTableBody');
    if (!tbody) return;

    const rows = [
        { name: 'Graph Coloring (Welsh-Powell)', complex: 'O(V² + E)', data: results.graph_coloring },
        { name: 'Greedy Heuristic', complex: 'O(n log n + n·s)', data: results.greedy },
        { name: 'Backtracking (Recursive DFS + MRV)', complex: 'O(mⁿ) Worst-case', data: results.backtracking },
        { name: 'Hybrid (Greedy + Backtracking)', complex: 'O(k·s + m^(n-k))', data: results.hybrid }
    ];

    tbody.innerHTML = rows.map(r => {
        const d = r.data;
        if (!d) return '';

        const isSuccess = d.success && d.unscheduled_classes === 0 && d.conflicts_count === 0;

        return `
            <tr>
                <td><strong>${r.name}</strong></td>
                <td><code>${r.complex}</code></td>
                <td><strong class="text-primary">${d.execution_time_ms} ms</strong></td>
                <td><strong class="text-success">${d.scheduled_classes} / ${d.total_classes}</strong></td>
                <td>${d.unscheduled_classes > 0 ? `<span class="badge-saas badge-saas-danger">${d.unscheduled_classes}</span>` : '0'}</td>
                <td>${d.backtracking_steps}</td>
                <td>${d.decisions_count}</td>
                <td>
                    <span class="badge-saas ${isSuccess ? 'badge-saas-success' : 'badge-saas-warning'}">
                        ${isSuccess ? '<i class="fa-solid fa-check"></i> 100% Conflict-Free' : '<i class="fa-solid fa-triangle-exclamation"></i> Partial Solution'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
}

// --------------------------------------------------------------------------
// HTML5 Canvas Welsh-Powell Conflict Network Graph Visualizer
// --------------------------------------------------------------------------
async function loadGraph() {
    try {
        const res = await fetch('/api/graph-data');
        const json = await res.json();
        if (json.status !== 'success' || !json.data) return;

        currentGraph = json.data;

        document.getElementById('graphVCount').innerText = currentGraph.vertex_count || 0;
        document.getElementById('graphECount').innerText = currentGraph.edge_count || 0;
        document.getElementById('graphChiCount').innerText = `${currentGraph.chromatic_number || 0} colors`;

        drawCanvasGraph(currentGraph);

    } catch (err) {
        console.error('Graph fetch error:', err);
    }
}

function drawCanvasGraph(graphData) {
    const canvas = document.getElementById('graphCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const vertices = graphData.vertices || [];
    const edges = graphData.edges || [];

    if (vertices.length === 0) {
        ctx.fillStyle = '#64748B';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No graph nodes available', width / 2, height / 2);
        return;
    }

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 40;

    const positions = {};
    const total = vertices.length;

    const palette = [
        '#315EAA', '#19B6B1', '#20A477', '#E6A23C', '#8B5CF6',
        '#EC4899', '#0EA5E9', '#F97316', '#6366F1', '#14B8A6'
    ];

    vertices.forEach((v, i) => {
        const angle = (i / total) * 2 * Math.PI - Math.PI / 2;
        positions[v.id] = {
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle),
            color: palette[v.color % palette.length],
            label: v.code || `V${v.id}`
        };
    });

    // 1. Draw Conflict Edges
    ctx.lineWidth = 0.6;
    edges.forEach(e => {
        const p1 = positions[e.source];
        const p2 = positions[e.target];
        if (p1 && p2) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = 'rgba(203, 213, 225, 0.45)';
            ctx.stroke();
        }
    });

    // 2. Draw Vertices
    vertices.forEach(v => {
        const pos = positions[v.id];
        if (!pos) return;

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 7, 0, 2 * Math.PI);
        ctx.fillStyle = pos.color;
        ctx.fill();

        ctx.lineWidth = 2;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();
    });

    // 3. Draw Labels (for alternating nodes)
    ctx.font = '10px JetBrains Mono';
    ctx.fillStyle = '#263449';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    vertices.forEach((v, i) => {
        if (i % 2 === 0) {
            const pos = positions[v.id];
            const textY = pos.y > centerY ? pos.y + 14 : pos.y - 12;
            ctx.fillText(pos.label, pos.x, textY);
        }
    });
}
