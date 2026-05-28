# New Jersey Superintendent Salaries Dashboard

This project publishes a searchable database and reporter copy generator for New Jersey superintendent salary data.

The site has two main pages:

- **Database dashboard:** Search, filter and browse superintendent salary records.
- **Reporter top 10 generator:** Select counties and generate a copy-ready top 10 list for a story.

## Live pages

Main database:

https://culleryusatrepos.github.io/NJSuperSalaries/

Reporter top 10 generator:

https://culleryusatrepos.github.io/NJSuperSalaries/reporter_top10.html

## How to use the database dashboard

Open the main dashboard page:

https://culleryusatrepos.github.io/NJSuperSalaries/

Use the search and filter tools to narrow the data by county, district, superintendent or other available fields.

The table can be used to compare superintendent salary records across New Jersey. The dashboard is meant as a quick lookup tool for reporters who need to identify high salaries, compare districts or find records from specific counties.

To move from the database to the story-writing tool, click:

**Open reporter top 10 generator**

## How to use the reporter top 10 generator

Open the reporter generator page:

https://culleryusatrepos.github.io/NJSuperSalaries/reporter_top10.html

The generator lets a reporter:

1. Select one or more counties.
2. Choose what to rank by.
3. Choose which details should appear in each bullet.
4. Generate a copy-ready list.
5. Copy the output as HTML, plain bullets, or formatted headline plus bullets.

The **Copy headline + bullets** button is usually the best option for pasting into a document editor because it preserves the headline and bullet formatting.

The **Copy HTML** button is useful if the list will be pasted into a web CMS or HTML editor.

The **Copy bullet list** button copies a plain-text version.

To return to the full database, click:

**Back to database**

## Data files

The dashboard is powered by these files in the `docs` folder:

- `docs/superintendent_salaries.csv`
- `docs/superintendent_salaries.json`

The public GitHub Pages site reads from the JSON file.

## Project structure

NJSuperSalaries/
  docs/
    index.html
    reporter_top10.html
    superintendent_salaries.csv
    superintendent_salaries.json
  scripts/
  README.md

## Local testing

Because the HTML pages load local JSON data, they should be tested with a local server instead of opening the files directly.

From the project root, run:

python -m http.server 8000

Then open:

http://localhost:8000/docs/index.html

or:

http://localhost:8000/docs/reporter_top10.html

Stop the local server with Ctrl+C.

## Publishing updates

After editing files, commit and push to GitHub:

git status
git add docs README.md
git commit -m "Update dashboard documentation"
git push origin main

GitHub Pages will rebuild from the `docs` folder.

## Source data

The original New Jersey superintendent salary files were downloaded from the New Jersey Department of Education's User Friendly Budget page:

https://www.nj.gov/education/budget/ufb/

The dashboard uses cleaned/exported versions of the source data in the `docs` folder:

- `docs/superintendent_salaries.csv`
- `docs/superintendent_salaries.json`

The original downloaded files are not required for the public GitHub Pages site to run. The public site reads from the cleaned JSON file.
