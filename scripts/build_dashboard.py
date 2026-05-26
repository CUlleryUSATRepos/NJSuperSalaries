import json
import pandas as pd
from pathlib import Path

SOURCE_URL = "https://www.nj.gov/education/budget/ufb/2526/download/employees26.csv"

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)

print("Downloading NJ employee salary CSV...")
df = pd.read_csv(SOURCE_URL, dtype=str)

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

# Keep only actual superintendent records.
# This matches the clean NJ title values:
# Superintendent and Assistant Superintendent.
supes = df[
    df["emp_job_title"].fillna("").str.contains("Superint", case=False, na=False)
].copy()

def money_to_number(value):
    if pd.isna(value):
        return 0.0
    value = str(value).replace("$", "").replace(",", "").strip()
    if value == "" or value.lower() == "nan":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0

def money_display(value):
    num = money_to_number(value)
    if num == 0:
        return "0"
    return f"${num:,.0f}"

money_cols = [
    "emp_base_salary",
    "total_allowances",
    "total_bonuses",
    "total_stipends",
    "total_insurance",
    "total_retirement_plan",
    "total_post_employment_benefits",
    "total_remuneration",
]

for col in money_cols:
    if col in supes.columns:
        supes[col + "_num"] = supes[col].apply(money_to_number)

known_comp_cols = [
    "emp_base_salary_num",
    "total_allowances_num",
    "total_bonuses_num",
    "total_stipends_num",
    "total_insurance_num",
    "total_retirement_plan_num",
    "total_post_employment_benefits_num",
    "total_remuneration_num",
]

for col in known_comp_cols:
    if col not in supes.columns:
        supes[col] = 0.0

supes["known_listed_compensation_num"] = supes[known_comp_cols].sum(axis=1)
supes["known_listed_compensation"] = supes["known_listed_compensation_num"].apply(lambda x: f"${x:,.0f}")

for col in money_cols:
    if col in supes.columns:
        supes[col] = supes[col].apply(money_display)

display_cols = [
    "county_id",
    "district_id",
    "coname",
    "distname",
    "emp_name",
    "emp_job_title",
    "emp_job_title_2",
    "emp_base_salary",
    "emp_base_salary_num",
    "known_listed_compensation",
    "known_listed_compensation_num",
    "emp_fte",
    "emp_shared",
    "emp_begin_date",
    "emp_end_date",
    "emp_work_day",
    "emp_vaca_day",
    "emp_sick_day",
    "emp_persn_day",
    "emp_cnslt_day",
    "total_allowances",
    "total_allowances_num",
    "total_bonuses",
    "total_bonuses_num",
    "total_stipends",
    "total_stipends_num",
    "total_insurance",
    "total_insurance_num",
    "total_retirement_plan",
    "total_retirement_plan_num",
    "total_post_employment_benefits",
    "total_post_employment_benefits_num",
    "total_remuneration",
    "total_remuneration_num",
]

existing_cols = [col for col in display_cols if col in supes.columns]
supes = supes[existing_cols].fillna("")

supes = supes.sort_values(
    by="emp_base_salary_num",
    ascending=False
)

records = supes.to_dict(orient="records")

supes.to_csv(OUT_DIR / "superintendent_salaries.csv", index=False)

with open(OUT_DIR / "superintendent_salaries.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False)

html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>New Jersey Superintendent Salaries</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f5f5f5;
      color: #222;
    }

    header {
      background: #102a43;
      color: white;
      padding: 24px;
    }

    header h1 {
      margin: 0 0 8px;
      font-size: 28px;
    }

    header p {
      margin: 0;
      max-width: 980px;
      line-height: 1.45;
      color: #d9e2ec;
    }

    main {
      padding: 20px;
    }

    .note {
      background: #fff8e1;
      border: 1px solid #f0d98c;
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 16px;
      line-height: 1.45;
      font-size: 14px;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .card {
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      padding: 12px;
    }

    .card .label {
      color: #52606d;
      font-size: 13px;
      margin-bottom: 4px;
    }

    .card .value {
      font-size: 20px;
      font-weight: bold;
    }

    .controls {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      gap: 12px;
      margin-bottom: 16px;
    }

    input, select {
      padding: 10px;
      font-size: 15px;
      border: 1px solid #bcccdc;
      border-radius: 6px;
      background: white;
    }

    .summary {
      margin-bottom: 14px;
      font-weight: bold;
    }

    .pagination {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
    }

    .pagination button {
      padding: 8px 12px;
      border: 1px solid #bcccdc;
      border-radius: 6px;
      background: white;
      cursor: pointer;
      font-size: 14px;
    }

    .pagination button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }

    #pageInfo {
      font-size: 14px;
      color: #334e68;
    }

    .table-wrap {
      overflow-x: auto;
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
    }

    table {
      border-collapse: collapse;
      width: 100%;
      min-width: 1700px;
    }

    th, td {
      padding: 9px;
      border-bottom: 1px solid #e6e6e6;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }

    th {
      background: #eef2f7;
      cursor: pointer;
      position: sticky;
      top: 0;
      z-index: 1;
      white-space: nowrap;
    }

    tr:hover {
      background: #f8fafc;
    }

    .money, .number {
      text-align: right;
      white-space: nowrap;
    }

    footer {
      padding: 20px;
      color: #666;
      font-size: 13px;
      line-height: 1.4;
    }

    @media (max-width: 900px) {
      .controls, .cards {
        grid-template-columns: 1fr;
      }

      header h1 {
        font-size: 22px;
      }
    }
  </style>
</head>

<body>
  <header>
    <h1>New Jersey Superintendent Salaries</h1>
    <p>
      Searchable database of New Jersey superintendent and assistant superintendent salary records
      from the 2025-26 NJ Department of Education User Friendly Budget administrative salaries and benefits file.
    </p>
  </header>

  <main>
    <div class="note">
      <strong>Note:</strong> “Known listed compensation” is a dashboard calculation that adds the salary and benefit fields available in the state file:
      base salary, allowances, bonuses, stipends, insurance contributions above the teacher contract, retirement-plan contributions above the teacher contract,
      post-employment benefits, and other/in-kind remuneration. The state file labels the last bucket as other/in-kind remuneration, so it should not be read as total compensation by itself.
    </div>

    <div class="cards">
      <div class="card">
        <div class="label">Records</div>
        <div class="value" id="cardRecords">—</div>
      </div>
      <div class="card">
        <div class="label">Average base salary</div>
        <div class="value" id="cardAverageBase">—</div>
      </div>
      <div class="card">
        <div class="label">Highest base salary</div>
        <div class="value" id="cardHighestBase">—</div>
      </div>
      <div class="card">
        <div class="label">Shared records</div>
        <div class="value" id="cardShared">—</div>
      </div>
    </div>

    <div class="controls">
      <input id="searchBox" type="search" placeholder="Search by name, district, county or job title...">
      <select id="countyFilter">
        <option value="">All counties</option>
      </select>
      <select id="titleFilter">
        <option value="">All superintendent titles</option>
      </select>
    </div>

    <div class="summary" id="summary">Loading records...</div>

    <div class="pagination">
      <button id="prevPage" type="button">Previous</button>
      <span id="pageInfo">Page 1</span>
      <button id="nextPage" type="button">Next</button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr id="tableHead"></tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </main>

  <footer>
    Source: New Jersey Department of Education, 2025-26 User Friendly Budget Summaries, employees26.csv —
    Select Administrative Salaries and Benefits.
  </footer>

  <script>
    let rows = [];
    let currentSort = "emp_base_salary_num";
    let sortDirection = "desc";
    let currentPage = 1;
    const rowsPerPage = 15;

    const columns = [
      {key: "emp_base_salary", sort: "emp_base_salary_num", label: "Base salary", className: "money"},
      {key: "known_listed_compensation", sort: "known_listed_compensation_num", label: "Known listed compensation", className: "money"},
      {key: "emp_name", sort: "emp_name", label: "Name"},
      {key: "emp_job_title", sort: "emp_job_title", label: "Job title"},
      {key: "coname", sort: "coname", label: "County"},
      {key: "distname", sort: "distname", label: "District"},
      {key: "emp_fte", sort: "emp_fte", label: "Full-time equivalent", className: "number"},
      {key: "emp_shared", sort: "emp_shared", label: "Shared with another district?"},
      {key: "emp_begin_date", sort: "emp_begin_date", label: "Contract begins"},
      {key: "emp_end_date", sort: "emp_end_date", label: "Contract ends"},
      {key: "emp_work_day", sort: "emp_work_day", label: "Work days", className: "number"},
      {key: "emp_vaca_day", sort: "emp_vaca_day", label: "Vacation days", className: "number"},
      {key: "emp_sick_day", sort: "emp_sick_day", label: "Sick days", className: "number"},
      {key: "emp_persn_day", sort: "emp_persn_day", label: "Personal days", className: "number"},
      {key: "emp_cnslt_day", sort: "emp_cnslt_day", label: "Consulting days", className: "number"},
      {key: "total_allowances", sort: "total_allowances_num", label: "Allowances", className: "money"},
      {key: "total_bonuses", sort: "total_bonuses_num", label: "Bonuses", className: "money"},
      {key: "total_stipends", sort: "total_stipends_num", label: "Stipends", className: "money"},
      {key: "total_insurance", sort: "total_insurance_num", label: "Insurance above teacher contract", className: "money"},
      {key: "total_retirement_plan", sort: "total_retirement_plan_num", label: "Retirement above teacher contract", className: "money"},
      {key: "total_post_employment_benefits", sort: "total_post_employment_benefits_num", label: "Post-employment benefits", className: "money"},
      {key: "total_remuneration", sort: "total_remuneration_num", label: "Other / in-kind remuneration", className: "money"}
    ];

    const searchBox = document.getElementById("searchBox");
    const countyFilter = document.getElementById("countyFilter");
    const titleFilter = document.getElementById("titleFilter");
    const tableHead = document.getElementById("tableHead");
    const tableBody = document.getElementById("tableBody");
    const summary = document.getElementById("summary");
    const prevPage = document.getElementById("prevPage");
    const nextPage = document.getElementById("nextPage");
    const pageInfo = document.getElementById("pageInfo");

    function formatMoneyNumber(value) {
      const num = Number(value || 0);
      return "$" + num.toLocaleString(undefined, {maximumFractionDigits: 0});
    }

    function uniqueValues(key) {
      return [...new Set(rows.map(row => row[key]).filter(Boolean))].sort();
    }

    function fillFilters() {
      countyFilter.innerHTML = '<option value="">All counties</option>';
      titleFilter.innerHTML = '<option value="">All superintendent titles</option>';

      uniqueValues("coname").forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        countyFilter.appendChild(option);
      });

      uniqueValues("emp_job_title").forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        titleFilter.appendChild(option);
      });
    }

    function renderHeader() {
      tableHead.innerHTML = columns.map(col => `
        <th data-sort="${col.sort}">${col.label}</th>
      `).join("");

      document.querySelectorAll("th[data-sort]").forEach(th => {
        th.addEventListener("click", () => {
          const key = th.dataset.sort;

          if (currentSort === key) {
            sortDirection = sortDirection === "asc" ? "desc" : "asc";
          } else {
            currentSort = key;
            sortDirection = "asc";
          }

          render();
        });
      });
    }

    function getFilteredRows() {
      const q = searchBox.value.toLowerCase().trim();
      const county = countyFilter.value;
      const title = titleFilter.value;

      return rows.filter(row => {
        const searchText = [
          row.emp_name,
          row.coname,
          row.distname,
          row.emp_job_title,
          row.emp_job_title_2,
          row.county_id,
          row.district_id
        ].join(" ").toLowerCase();

        const matchesSearch = q === "" || searchText.includes(q);
        const matchesCounty = county === "" || row.coname === county;
        const matchesTitle = title === "" || row.emp_job_title === title;

        return matchesSearch && matchesCounty && matchesTitle;
      });
    }

    function sortRows(data) {
      return data.sort((a, b) => {
        let av = a[currentSort] ?? "";
        let bv = b[currentSort] ?? "";

        const an = Number(av);
        const bn = Number(bv);

        if (!Number.isNaN(an) && !Number.isNaN(bn)) {
          return sortDirection === "asc" ? an - bn : bn - an;
        }

        av = String(av).toLowerCase();
        bv = String(bv).toLowerCase();

        if (av < bv) return sortDirection === "asc" ? -1 : 1;
        if (av > bv) return sortDirection === "asc" ? 1 : -1;
        return 0;
      });
    }

    function updateCards(filtered) {
      const count = filtered.length;
      const sharedCount = filtered.filter(row => String(row.emp_shared || "").toUpperCase() === "Y").length;
      const baseValues = filtered.map(row => Number(row.emp_base_salary_num || 0)).filter(value => value > 0);
      const avgBase = baseValues.length ? baseValues.reduce((a, b) => a + b, 0) / baseValues.length : 0;
      const maxBase = baseValues.length ? Math.max(...baseValues) : 0;

      document.getElementById("cardRecords").textContent = count.toLocaleString();
      document.getElementById("cardAverageBase").textContent = formatMoneyNumber(avgBase);
      document.getElementById("cardHighestBase").textContent = formatMoneyNumber(maxBase);
      document.getElementById("cardShared").textContent = sharedCount.toLocaleString();
    }

    function render() {
      const filtered = sortRows(getFilteredRows());

      const totalRows = filtered.length;
      const totalPages = Math.max(1, Math.ceil(totalRows / rowsPerPage));

      if (currentPage > totalPages) {
        currentPage = totalPages;
      }

      const startIndex = (currentPage - 1) * rowsPerPage;
      const endIndex = startIndex + rowsPerPage;
      const pageRows = filtered.slice(startIndex, endIndex);

      const shownStart = totalRows === 0 ? 0 : startIndex + 1;
      const shownEnd = Math.min(endIndex, totalRows);

      summary.textContent = `${shownStart.toLocaleString()}-${shownEnd.toLocaleString()} of ${totalRows.toLocaleString()} records shown`;
      pageInfo.textContent = `Page ${currentPage.toLocaleString()} of ${totalPages.toLocaleString()}`;

      prevPage.disabled = currentPage <= 1;
      nextPage.disabled = currentPage >= totalPages;

      updateCards(filtered);

      tableBody.innerHTML = pageRows.map(row => `
        <tr>
          ${columns.map(col => {
            let value = row[col.key] ?? "";
            if (col.key === "emp_job_title" && row.emp_job_title_2) {
              value = `${row.emp_job_title || ""} / ${row.emp_job_title_2}`;
            }
            return `<td class="${col.className || ""}">${value}</td>`;
          }).join("")}
        </tr>
      `).join("");
    }

    searchBox.addEventListener("input", () => {
      currentPage = 1;
      render();
    });

    countyFilter.addEventListener("change", () => {
      currentPage = 1;
      render();
    });

    titleFilter.addEventListener("change", () => {
      currentPage = 1;
      render();
    });

    prevPage.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage -= 1;
        render();
      }
    });

    nextPage.addEventListener("click", () => {
      currentPage += 1;
      render();
    });

    fetch("superintendent_salaries.json")
      .then(response => response.json())
      .then(data => {
        rows = data;
        renderHeader();
        fillFilters();
        render();
      })
      .catch(error => {
        console.error(error);
        summary.textContent = "Could not load superintendent_salaries.json. Make sure you are viewing this through a local server or GitHub Pages.";
      });
  </script>
</body>
</html>
"""

(OUT_DIR / "index.html").write_text(html, encoding="utf-8")

print(f"Done. Wrote {len(supes):,} superintendent-related records.")
print("Dashboard: docs/index.html")
print("Filtered CSV: docs/superintendent_salaries.csv")
print("Filtered JSON: docs/superintendent_salaries.json")

