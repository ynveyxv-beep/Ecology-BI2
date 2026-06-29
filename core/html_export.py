import json


class HTMLExporter:

    @staticmethod
    def export(pages, path):

        pages_data = []

        # ---------------- SERIALIZE ----------------
        for p_index, page in enumerate(pages):

            charts = []

            for c_index, item in enumerate(page.items):

                if not hasattr(item, "df"):
                    continue

                df = item.df
                if df is None:
                    continue

                x = item.x_col
                y = item.y_col

                if x is None or y is None:
                    continue

                charts.append({
                    "id": f"p{p_index}_c{c_index}",
                    "x": x,
                    "y": y,
                    "data": df[[x, y]].to_dict("records")
                })

            pages_data.append({
                "name": getattr(page, "name", f"Page {p_index+1}"),
                "charts": charts
            })

        # ---------------- HTML ----------------
        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<style>
body {{
    font-family: Arial;
    margin: 0;
}}

#header {{
    display: flex;
    gap: 10px;
    padding: 10px;
    background: #222;
    color: white;
    align-items: center;
}}

#tabs {{
    display: flex;
    gap: 10px;
}}

.tab {{
    padding: 6px 12px;
    background: #444;
    cursor: pointer;
    border-radius: 5px;
}}

.tab:hover {{
    background: #666;
}}

#content {{
    padding: 20px;
}}

.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}}

.card {{
    border: 1px solid #ddd;
    padding: 10px;
    border-radius: 8px;
}}
</style>
</head>

<body>

<div id="header">
    <button onclick="drillBack()">⬅ Back</button>
    <div id="tabs"></div>
</div>

<div id="content"></div>

<script>

const pages = {json.dumps(pages_data)};

let currentPage = 0;

// STATE
let globalFilters = {{}};
let drillStack = [];

// FILTER ENGINE
function applyFilters(data) {{
    let result = data;

    Object.keys(globalFilters).forEach(key => {{
        result = result.filter(r =>
            String(r[key]) === String(globalFilters[key])
        );
    }});

    return result;
}}

// TABS
function renderTabs() {{
    const tabs = document.getElementById("tabs");
    tabs.innerHTML = "";

    pages.forEach((p, i) => {{
        const t = document.createElement("div");
        t.className = "tab";
        t.innerText = p.name;

        t.onclick = () => {{
            currentPage = i;
            render();
        }};

        tabs.appendChild(t);
    }});
}}

// DRILL BACK
function drillBack() {{
    if (drillStack.length === 0) return;

    const last = drillStack.pop();
    delete globalFilters[last.level];

    render();
}}

// RENDER
function render() {{
    const page = pages[currentPage];
    const container = document.getElementById("content");

    container.innerHTML = "<div class='grid'></div>";

    const grid = container.querySelector(".grid");

    page.charts.forEach(chart => {{

        const div = document.createElement("div");
        div.className = "card";
        div.id = chart.id;

        grid.appendChild(div);

        let data = applyFilters(chart.data);

        const x = data.map(d => d[chart.x]);
        const y = data.map(d => d[chart.y]);

        Plotly.newPlot(chart.id, [
            {{
                x: x,
                y: y,
                mode: "markers",
                type: "scatter"
            }}
        ]);

        document.getElementById(chart.id).on('plotly_click', function(e) {{

            const pt = e.points[0];

            drillStack.push({{
                level: chart.x,
                value: pt.x
            }});

            globalFilters[chart.x] = pt.x;

            render();
        }});
    }});
}}

renderTabs();
render();

</script>

</body>
</html>
"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)