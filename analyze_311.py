from pathlib import Path

import duckdb

csv_path = Path("data/311_Service_Requests_from_2020_to_Present_20261123.csv")


if not csv_path.is_file():
    raise SystemExit(f"CSV file not found: {csv_path}. Check the filename in data/.")

query = """
SELECT
    TRIM("Problem (formerly Complaint Type)") AS problem,
    COUNT(*) AS request_count
FROM read_csv(?, header = true, all_varchar = true)
WHERE NULLIF(TRIM("Problem (formerly Complaint Type)"), '') IS NOT NULL
GROUP BY problem
ORDER BY request_count DESC, problem ASC
LIMIT 10
"""

with duckdb.connect() as connection:
    results = connection.execute(query, [str(csv_path)]).fetchall()

print("Top 10 NYC 311 problems by number of requests\n")
for rank, (problem, count) in enumerate(results, start=1):
    print(f"{rank:>2}. {problem}: {count:,}")