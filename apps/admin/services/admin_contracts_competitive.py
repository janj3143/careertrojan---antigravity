"""services.admin_contracts – Competitive Intelligence contracts (ADD)

These constants are used by Page 11 to hard-enforce backend payload shape.
Add them to your existing services.admin_contracts module.
"""

# Required keys in /admin/competitive/overview response
CI_OVERVIEW_REQUIRED_KEYS = [
    "kpis",               # dict
    "monitored_count",   # int
    "last_run",          # str|None
]

# Required keys in /admin/competitive/kpis.kpis dict
CI_KPI_KEYS = [
    "monitored_competitors",
    "signals_30d",
    "reports_30d",
    "tasks_running",
]

# Required keys per competitor entry
CI_COMPETITOR_KEYS = [
    "competitor_id",     # str
    "name",              # str
]

# Required keys per signal row
CI_SIGNAL_KEYS = [
    "date",              # str (YYYY-MM-DD)
    "signal",            # str
    "count",             # int
]

# Required keys per benchmark row
CI_BENCHMARK_KEYS = [
    "competitor_id",
    "dimension",
    "value",
]

# Required keys per task entry
CI_TASK_KEYS = [
    "task_id",
    "type",
    "status",
    "created_at",
]

# Required keys per report entry
CI_REPORT_KEYS = [
    "report_id",
    "title",
    "created_at",
]
