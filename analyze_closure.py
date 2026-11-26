from pathlib import Path

import duckdb

csv_path = (
    Path(__file__).resolve().parent
    / "data"
    / "311_Service_Requests_from_2020_to_Present_20261123.csv"
)

query = """
WITH requests AS (
    SELECT
        NULLIF(TRIM("Problem (formerly Complaint Type)"), '') AS problem,
        TRY_STRPTIME(TRIM("Created Date"), '%m/%d/%Y %I:%M:%S %p') AS created_at,
        NULLIF(TRIM("Closed Date"), '') AS closed_text,
        TRY_STRPTIME(TRIM("Closed Date"), '%m/%d/%Y %I:%M:%S %p') AS closed_at
    FROM read_csv(?, header = true, all_varchar = true)
),
timings AS (
    SELECT
        problem,
        closed_text,
        CASE
            WHEN closed_at >= created_at
            THEN DATE_DIFF('second', created_at, closed_at) / 3600.0
        END AS hours_to_close
    FROM requests
    WHERE problem IS NOT NULL
)
SELECT
    problem,
    COUNT(*) AS total_requests,
    COUNT(hours_to_close) AS timed_requests,
    COUNT(*) FILTER (WHERE closed_text IS NULL) AS missing_close_date,
    ROUND(MEDIAN(hours_to_close), 2) AS median_hours
FROM timings
GROUP BY problem
ORDER BY total_requests DESC, problem ASC
LIMIT 10
"""

with duckdb.connect() as connection:
    results = connection.execute(query, [str(csv_path)]).fetchall()

for problem, total, timed, missing, median in results:
    median_text = f"{median:,.2f} hours" if median is not None else "Unavailable"
    invalid = total - timed - missing

    print(f"\n{problem}")
    print(f"  Total requests: {total:,}")
    print(f"  Requests used for timing: {timed:,}")
    print(f"  Missing closing date: {missing:,}")
    print(f"  Unusable timestamps: {invalid:,}")
    print(f"  Median time to close: {median_text}")

import matplotlib.pyplot as plt

chart_rows = sorted(
    [(problem, median) for problem, _, _, _, median in results if median is not None],
    key=lambda row: row[1],
)
problems = [problem for problem, _ in chart_rows]
hours = [median for _, median in chart_rows]

output_dir = Path(__file__).resolve().parent / "outputs"
output_dir.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
bars = ax.barh(problems, hours, color="#246A8D")
ax.bar_label(bars, fmt="%.2f h", padding=4)
ax.set_xlim(0, max(hours) * 1.18)
ax.set_title("NYC 311: Median Time to Close by Problem Type")
ax.set_xlabel("Median hours to recorded closure")

chart_path = output_dir / "median_closure_hours.png"
fig.savefig(chart_path, dpi=160)
plt.close(fig)

print(f"\nChart saved to {chart_path}")