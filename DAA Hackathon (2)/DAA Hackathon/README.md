# Smart College Timetable Generator (SaaS DAA Edition)

An enterprise-grade, intelligent college timetable generation and substitution management platform developed for academic institutions. The system automatically produces 100% conflict-free weekly schedules using core **Design and Analysis of Algorithms (DAA)** techniques.

The user experience and visual design are inspired by commercial academic platforms:
* **Edumerge**: College Timetable and Faculty Substitution Management.
* **Blink**: AI Smart Classroom and Timetable Scheduler.
* **Omniscol**: Visual multi-dimensional calendar and school schedule management.

---

## 1. System Architecture & Features

### Core DAA Algorithms
1. **Graph Coloring Algorithm (Welsh-Powell)**
   - Models class sessions as vertices $V$.
   - Constructs interference edges $E$ for sessions that share faculty, student batches, or specialized laboratory facilities.
   - Treats discrete time slots as colors.
   - Computes the chromatic number $\chi(G)$ to ensure conflict-free chromatic partitioning.
   - Features real-time HTML5 Canvas conflict network topology visualization.

2. **Greedy Scheduling Algorithm**
   - Applies the Most Constrained Variable (MCV) heuristic.
   - Prioritizes computing labs, high-priority subjects, and high-strength student cohorts.
   - Greedily assigns each class session to the earliest valid time slot and room with minimal penalty.
   - Logs decision paths and any unscheduled overflow sessions.

3. **Backtracking Algorithm**
   - Implements recursive depth-first tree search.
   - Employs Minimum Remaining Values (MRV) and forward checking.
   - Systematically reverts state (backtracks) upon encountering hard constraint dead-ends.
   - Guarantees an exact, 100% valid schedule whenever one exists.

4. **Hybrid Scheduling (Greedy + Backtracking)**
   - Two-phase optimization: Greedily pre-allocates scarce lab resources and high-priority core subjects, then uses recursive depth-first backtracking to resolve remaining courses.

---

## 2. Hard Constraints Enforced
* **Zero Faculty Clashes**: No faculty member is scheduled to teach two classes at the same time.
* **Zero Classroom Double-Bookings**: No room or lab is booked for multiple simultaneous classes.
* **Zero Student Batch Clashes**: No student cohort has overlapping class periods.
* **Faculty Availability & Blocked Hours**: Respects individual professor unavailable periods (research, meetings, leave).
* **Classroom Seating Capacity**: Enforces Room Capacity $\ge$ Batch Student Strength.
* **Lab Facility Matching**: Practical and Computing lab courses are strictly placed in equipped Lab spaces, not normal lecture halls.
* **Pedagogical Balance**: Enforces a maximum of 2 sessions of any given subject per day per batch.

---

## 3. UI/UX Design System
* **Sophisticated Light SaaS Palette**:
  - Page Background: `#F5F7FA`
  - Fixed Sidebar: `#17243A`
  - Primary Brand: `#315EAA`
  - Accent Color: `#19B6B1`
  - Cards & Panels: `#FFFFFF`
  - Text: `#263449`
  - Success: `#20A477` | Warning: `#E6A23C` | Danger: `#E05252`
* **Typography**: Clean modern typefaces (`Inter`, `Poppins`, and `JetBrains Mono`).
* **Visual Timetable Calendar**:
  - Days as rows, teaching periods 1–6 as columns, dedicated Lunch Recess column.
  - Multi-dimensional filters (Batch-wise, Faculty-wise, Room-wise, Department-wise).
  - **Interactive Drag-and-Drop Editing**: Real-time constraint checking via REST API; invalid moves are caught with an explanatory alert toast.
* **Faculty Substitution Workbench (Edumerge-inspired)**:
  - Automatically identifies affected classes when a professor is absent.
  - Recommends candidate replacement faculty ranked by subject expertise, free time window, and workload headroom.
  - One-click admin approval immediately updates the live timetable and records audit logs.

---

## 4. Project Directory Structure

```
college-timetable-generator/
│
├── app.py                     # Main Flask application and Blueprint registry
├── config.py                  # Academic calendar, bell timings, and palette settings
├── requirements.txt           # Python package dependencies
├── test_suite.py              # Automated test suite (12 unit and integration tests)
├── README.md                  # System documentation
│
├── database/
│   ├── db.py                  # SQLite connection and problem data generator
│   ├── schema.sql             # SQL schema (users, batches, faculty, classrooms, timetable, etc.)
│   ├── seed.py                # Database population script with sample academic data
│   └── timetable.db           # SQLite database file
│
├── algorithms/
│   ├── __init__.py
│   ├── constraints.py         # Incremental constraint checker and full schedule auditor
│   ├── backtracking.py        # Recursive Backtracking solver with MRV
│   ├── greedy.py              # Greedy priority-sorted local search solver
│   ├── graph_coloring.py      # Welsh-Powell Graph Coloring solver & topology exporter
│   ├── hybrid.py              # Hybrid Greedy + Backtracking solver
│   └── comparison.py          # Unified multi-algorithm benchmark runner
│
├── routes/
│   ├── dashboard_routes.py    # Dashboard statistics, utilization, and activities
│   ├── timetable_routes.py    # Timetable querying, generation, and drag-drop moves
│   ├── faculty_routes.py      # Faculty management and availability matrix
│   ├── classroom_routes.py    # Classroom CRUD, schedule modal, and utilization
│   ├── batch_routes.py        # Student batch CRUD and course associations
│   ├── subject_routes.py      # Academic subjects CRUD and priority management
│   ├── substitution_routes.py # Faculty substitution recommendations and approval
│   ├── conflict_routes.py     # Live 6-rule academic conflict auditor
│   ├── algorithm_routes.py    # Algorithm benchmark suite and graph topology data
│   └── report_routes.py       # Faculty workload, room utilization reports & CSV export
│
├── templates/
│   ├── base.html              # Fixed sidebar (#17243A) and topbar layout
│   ├── dashboard.html         # Admin overview, statistics cards, and Chart.js graphs
│   ├── timetable.html         # Interactive calendar grid with drag-and-drop
│   ├── generate.html          # Blink-inspired automated generation workspace
│   ├── substitution.html      # Edumerge-inspired substitution management page
│   ├── faculty.html           # Faculty management and details modal
│   ├── availability.html      # Interactive faculty availability matrix grid
│   ├── classrooms.html        # Classroom management and occupancy schedules
│   ├── batches.html           # Student batch management
│   ├── subjects.html          # Subject and course management
│   ├── conflicts.html         # Automated conflict auditor with remedial advice
│   ├── comparison.html        # DAA benchmark comparison and Canvas network graph
│   ├── reports.html           # Workload and utilization reports with CSV export
│   └── settings.html          # System preferences and academic timings
│
└── static/
    ├── css/
    │   └── style.css          # SaaS Light Theme stylesheet
    └── js/
        ├── dashboard.js       # Dashboard KPIs and Chart.js charts
        ├── timetable.js       # Calendar grid, filters, and drag-drop move handler
        ├── generate.js        # Timetable generation trigger and step trace modal
        ├── substitution.js    # Substitution recommendations and approvals
        └── algorithms.js      # Algorithm benchmarks and Canvas network visualizer
```

---

## 5. Installation & Execution

### Prerequisites
* Python 3.10+ (tested on Python 3.13)
* Standard browser (Chrome, Firefox, Edge, Safari)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Initialize and Seed the Database
```powershell
py -3.13 database/seed.py
```

### 3. Run the Automated Test Suite
```powershell
py -3.13 test_suite.py
```
*(All 12 test cases verifying constraints, algorithms, and APIs will run and output `OK`)*

### 4. Launch the Web Application
```powershell
py -3.13 app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 6. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/dashboard-stats` | `GET` | Aggregated KPI stats, room utilization, and workload feeds |
| `/api/generate-timetable` | `POST` | Executes selected algorithm (`backtracking`, `greedy`, `graph_coloring`, `hybrid`) |
| `/api/timetable` | `GET` | Retrieves timetable filtered by batch, faculty, room, or department |
| `/api/timetable/move` | `PUT` | Validates and persists drag-and-drop session moves |
| `/api/conflicts` | `GET` | Audits current timetable across all 6 constraints |
| `/api/compare-algorithms` | `POST` | Executes all 4 algorithms on identical data and returns benchmarks |
| `/api/graph-data` | `GET` | Exports Welsh-Powell node-link conflict topology for canvas rendering |
| `/api/substitution/recommendations` | `GET` | Calculates ranked candidate substitutes for an absent faculty member |
| `/api/substitutions` | `POST` | Logs faculty substitution and reassigns timetable session |
| `/api/reports/export-csv/<type>` | `GET` | Downloads CSV export (`timetable`, `faculty_workload`, `classrooms`) |

---

## 7. License
Developed for educational, university scheduling, and academic algorithm research purposes.
