import json
import pandas as pd
from pathlib import Path

EMPLOYEE_URL = "https://www.nj.gov/education/budget/ufb/2526/download/employees26.csv"
SHARED_URL = "https://www.nj.gov/education/budget/ufb/2526/download/shared26.csv"

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)

print("Downloading salary file...")
a1 = pd.read_csv(EMPLOYEE_URL, dtype=str)

print("Downloading shared-services file...")
b1 = pd.read_csv(SHARED_URL, dtype=str)

def clean_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df

a1 = clean_columns(a1)
b1 = clean_columns(b1)

def clean_id(series, width):
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(width)
    )

a1["county_id"] = clean_id(a1["county_id"], 2)
a1["district_id"] = clean_id(a1["district_id"], 4)

b1["county_id"] = clean_id(b1["county_id"], 2)
b1["district_id"] = clean_id(b1["district_id"], 4)

# Keep only actual full-time superintendent records.
supes = a1[
    a1["emp_job_title"].fillna("").str.contains("Superint", case=False, na=False)
].copy()

supes["_emp_fte_num"] = pd.to_numeric(supes["emp_fte"], errors="coerce")
supes = supes[
    supes["_emp_fte_num"].eq(1)
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

# Focus shared-services notes on the superintendent/assistant superintendent category.
shared_super = b1[
    b1["shrd_srvc_cat_type"].fillna("").str.strip().eq("Superintendent and Assistant Sup.")
].copy()

shared_super["desc_clean"] = (
    shared_super["shrd_srvc_cat_desc"]
    .fillna("")
    .astype(str)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

shared_super["amount_num"] = shared_super["shrd_srvc_cat_amount"].apply(money_to_number)

def combine_notes(group):
    notes = [
        note for note in group["desc_clean"].dropna().astype(str).tolist()
        if note.strip()
    ]

    notes = list(dict.fromkeys(notes))
    return " | ".join(notes[:3])

direct_notes = (
    shared_super
    .groupby(["county_id", "district_id"], as_index=False)
    .agg(
        direct_shared_note=("desc_clean", lambda x: " | ".join(list(dict.fromkeys([str(v).strip() for v in x if str(v).strip()]))[:3])),
        direct_shared_amount=("amount_num", "sum")
    )
)

supes = supes.merge(
    direct_notes,
    on=["county_id", "district_id"],
    how="left"
)

generic_words = {
    "co", "county", "vocational", "special", "service", "services",
    "school", "schools", "district", "public", "regional", "boro",
    "borough", "twp", "township", "city", "elementary", "high",
    "board", "education", "boe"
}

def district_search_terms(name):
    name = str(name).replace("-", " ").replace(".", " ").strip()
    parts = [p.strip() for p in name.split() if p.strip()]
    useful = [
        p for p in parts
        if p.lower() not in generic_words and len(p) >= 4
    ]

    terms = []

    # Try fuller district name first.
    if name:
        terms.append(name)

    # Then try useful words.
    terms.extend(useful[:3])

    # Preserve order and remove duplicates.
    return list(dict.fromkeys(terms))

def find_partner_note(row):
    if str(row.get("emp_shared", "")).upper() != "Y":
        return "", 0.0

    if pd.notna(row.get("direct_shared_note")) and str(row.get("direct_shared_note")).strip():
        return "", 0.0

    county_id = row.get("county_id", "")
    district_id = row.get("district_id", "")
    distname = row.get("distname", "")

    possible_rows = shared_super[
        (shared_super["county_id"] == county_id)
        & (shared_super["district_id"] != district_id)
    ].copy()

    terms = district_search_terms(distname)

    matches = []

    for _, shared_row in possible_rows.iterrows():
        desc = str(shared_row.get("desc_clean", ""))
        for term in terms:
            if term and term.lower() in desc.lower():
                matches.append(shared_row)
                break

    if not matches:
        return "", 0.0

    notes = []
    amount_total = 0.0

    for shared_row in matches[:3]:
        partner_district = shared_row.get("district_name", "")
        desc = shared_row.get("desc_clean", "")
        amount_total += money_to_number(shared_row.get("shrd_srvc_cat_amount", 0))

        notes.append(f"Possible partner note from {partner_district}: {desc}")

    return " | ".join(notes), amount_total

partner_results = supes.apply(find_partner_note, axis=1, result_type="expand")
supes["partner_shared_note"] = partner_results[0]
supes["partner_shared_amount"] = partner_results[1]

def pick_shared_status(row):
    if str(row.get("emp_shared", "")).upper() != "Y":
        return ""

    if pd.notna(row.get("direct_shared_note")) and str(row.get("direct_shared_note")).strip():
        return "Direct shared-services note"

    if str(row.get("partner_shared_note", "")).strip():
        return "Possible partner shared-services note"

    return "Marked shared in salary file; no shared-services note found"

def pick_shared_note(row):
    if str(row.get("direct_shared_note", "")).strip():
        return row["direct_shared_note"]

    if str(row.get("partner_shared_note", "")).strip():
        return row["partner_shared_note"]

    if str(row.get("emp_shared", "")).upper() == "Y":
        return "The salary file marks this record as shared, but no superintendent shared-services note was matched."

    return ""

def pick_shared_amount(row):
    direct_amount = money_to_number(row.get("direct_shared_amount", 0))
    partner_amount = money_to_number(row.get("partner_shared_amount", 0))

    if direct_amount:
        return direct_amount
    if partner_amount:
        return partner_amount
    return 0.0

supes["shared_context_status"] = supes.apply(pick_shared_status, axis=1)
supes["shared_context_note"] = supes.apply(pick_shared_note, axis=1)
supes["shared_context_amount_num"] = supes.apply(pick_shared_amount, axis=1)
supes["shared_context_amount"] = supes["shared_context_amount_num"].apply(lambda x: f"${x:,.0f}" if x else "0")

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
    "shared_context_status",
    "shared_context_note",
    "shared_context_amount",
    "shared_context_amount_num",
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

print(f"Done. Wrote {len(supes):,} superintendent-related records.")
print()
print("Shared-context status counts:")
print(supes["shared_context_status"].replace("", pd.NA).value_counts(dropna=True))
print()
print("Dashboard data written:")
print("docs/superintendent_salaries.csv")
print("docs/superintendent_salaries.json")

