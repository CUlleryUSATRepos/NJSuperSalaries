from pathlib import Path
import json
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "story-embed"

SOURCE_CSV = DOCS / "superintendent_salaries.csv"

OUT_CSV = OUT_DIR / "nj_superintendent_salary_embed.csv"
OUT_JSON = OUT_DIR / "nj_superintendent_salary_embed.json"
OUT_HTML = OUT_DIR / "index.html"


def money(value):
    if pd.isna(value):
        return ""
    return "${:,.0f}".format(float(value))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(SOURCE_CSV)

    # Keep actual superintendents only. This excludes Assistant Superintendent rows.
    df = df[
        df["emp_job_title"].astype(str).str.strip().str.lower() == "superintendent"
    ].copy()

    df = df.sort_values(
        by=["emp_base_salary_num", "known_listed_compensation_num"],
        ascending=[False, False]
    ).reset_index(drop=True)

    df["Rank"] = df["emp_base_salary_num"].rank(
        method="min",
        ascending=False
    ).astype(int)

    embed = pd.DataFrame({
        "Rank": df["Rank"],
        "Superintendent": df["emp_name"],
        "District": df["distname"],
        "County": df["coname"],
        "Base salary": df["emp_base_salary_num"].apply(money),
    })

    embed.to_csv(OUT_CSV, index=False)

    records = embed.to_dict(orient="records")
    OUT_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")

    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>New Jersey superintendent salaries</title>
<style>
  body {
    margin: 0;
    padding: 0;
    font-family: Arial, Helvetica, sans-serif;
    color: #222;
    background: #fff;
  }

  .salary-widget {
    max-width: 100%;
    padding: 8px;
    box-sizing: border-box;
  }

  h2 {
    font-size: 18px;
    line-height: 1.25;
    margin: 0 0 4px;
  }

  .note {
    font-size: 13px;
    line-height: 1.35;
    color: #666;
    margin: 0 0 10px;
  }

  #searchBox {
    width: 100%;
    box-sizing: border-box;
    padding: 9px 10px;
    font-size: 15px;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-bottom: 10px;
  }

  .table-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #ddd;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  th, td {
    padding: 8px 10px;
    border-bottom: 1px solid #ddd;
    text-align: left;
    vertical-align: top;
    white-space: nowrap;
  }

  th {
    background: #f4f4f4;
    cursor: pointer;
  }

  tbody tr:nth-child(even) {
    background: #f7f7f7;
  }

  tbody tr:nth-child(odd) {
    background: #ffffff;
  }

  tbody tr:hover {
    background: #eeeeee;
  }

  th:first-child,
  td:first-child,
  th:last-child,
  td:last-child {
    text-align: right;
  }

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-top: 10px;
    font-size: 13px;
  }

  .pagination button {
    padding: 6px 10px;
    border: 1px solid #ccc;
    background: #f4f4f4;
    border-radius: 4px;
    cursor: pointer;
  }

  .pagination button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .footer-note {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
    line-height: 1.35;
  }

  @media (max-width: 600px) {
    h2 {
      font-size: 16px;
    }

    table {
      font-size: 13px;
    }

    th, td {
      padding: 7px 8px;
    }
  }
</style>
</head>
<body>
<div class="salary-widget">
  <h2>Search New Jersey superintendent salaries</h2>
  <p class="note">Search by superintendent, district or county. Rankings are based on reported base salary.</p>

  <input id="searchBox" type="search" placeholder="Search superintendent, district or county">

  <div class="table-wrap">
    <table id="salaryTable">
      <thead>
        <tr>
          <th data-key="Rank">Rank</th>
          <th data-key="Superintendent">Superintendent</th>
          <th data-key="District">District</th>
          <th data-key="County">County</th>
          <th data-key="Base salary">Base salary</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="pagination">
    <button id="prevPage" type="button">Previous</button>
    <span id="pageInfo"></span>
    <button id="nextPage" type="button">Next</button>
  </div>

  <div class="footer-note">
    Source: New Jersey Department of Education user-friendly budget files.
  </div>
</div>

<script>
const DATA = __DATA__;

let currentData = [...DATA];
let sortKey = "Rank";
let sortDirection = "asc";
let currentPage = 1;
const rowsPerPage = 10;

const tbody = document.querySelector("#salaryTable tbody");
const searchBox = document.querySelector("#searchBox");
const prevPage = document.querySelector("#prevPage");
const nextPage = document.querySelector("#nextPage");
const pageInfo = document.querySelector("#pageInfo");

function parseMoney(value) {
  return Number(String(value).replace(/[$,]/g, "")) || 0;
}

function renderRows(rows) {
  tbody.innerHTML = "";

  rows.forEach(row => {
    const tr = document.createElement("tr");

    ["Rank", "Superintendent", "District", "County", "Base salary"].forEach(key => {
      const td = document.createElement("td");
      td.textContent = row[key] || "";
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
}

function sortRows(rows) {
  return [...rows].sort((a, b) => {
    let av = a[sortKey];
    let bv = b[sortKey];

    if (sortKey === "Rank") {
      av = Number(av);
      bv = Number(bv);
    } else if (sortKey === "Base salary") {
      av = parseMoney(av);
      bv = parseMoney(bv);
    } else {
      av = String(av || "").toLowerCase();
      bv = String(bv || "").toLowerCase();
    }

    if (av < bv) return sortDirection === "asc" ? -1 : 1;
    if (av > bv) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });
}

function renderPage(rows) {
  const totalPages = Math.max(1, Math.ceil(rows.length / rowsPerPage));

  if (currentPage > totalPages) {
    currentPage = totalPages;
  }

  const start = (currentPage - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageRows = rows.slice(start, end);

  renderRows(pageRows);

  pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  prevPage.disabled = currentPage === 1;
  nextPage.disabled = currentPage === totalPages;
}

function applySearchAndSort(resetPage = false) {
  if (resetPage) {
    currentPage = 1;
  }

  const term = searchBox.value.trim().toLowerCase();

  currentData = DATA.filter(row => {
    return (
      String(row.Superintendent || "").toLowerCase().includes(term) ||
      String(row.District || "").toLowerCase().includes(term) ||
      String(row.County || "").toLowerCase().includes(term)
    );
  });

  renderPage(sortRows(currentData));
}

searchBox.addEventListener("input", () => applySearchAndSort(true));

prevPage.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage -= 1;
    applySearchAndSort();
  }
});

nextPage.addEventListener("click", () => {
  const totalPages = Math.max(1, Math.ceil(currentData.length / rowsPerPage));

  if (currentPage < totalPages) {
    currentPage += 1;
    applySearchAndSort();
  }
});

document.querySelectorAll("th").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;

    if (sortKey === key) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      sortKey = key;
      sortDirection = key === "Rank" ? "asc" : "desc";
    }

    applySearchAndSort();
  });
});

applySearchAndSort();
</script>
</body>
</html>
"""

    html = html.replace("__DATA__", json.dumps(records))
    OUT_HTML.write_text(html, encoding="utf-8")

    print(f"Built: {OUT_HTML}")
    print(f"Built: {OUT_CSV}")
    print(f"Built: {OUT_JSON}")
    print(f"Rows: {len(embed)}")


if __name__ == "__main__":
    main()
