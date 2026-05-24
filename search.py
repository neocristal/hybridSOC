from flask import Flask, render_template_string, request
import requests
import spacy
import os
from duckduckgo_search import DDGS

app = Flask(__name__)

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Optional Bing API (leave empty if not using)
BING_API_KEY = os.environ.get("BING_API_KEY", "")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>OSINT Multi-Search</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        input, button { padding: 10px; margin: 5px; }
        .result { margin-top: 20px; }
        .box { border: 1px solid #ddd; padding: 15px; margin-top: 20px; border-radius: 8px; }
        .dork { cursor: pointer; color: blue; text-decoration: underline; display: block; margin: 5px 0; }
    </style>

    <script>
        function setQuery(q) {
            document.getElementById("query").value = q;
        }

        function appendQuery(q) {
            let input = document.getElementById("query");
            input.value += " " + q;
        }
    </script>
</head>
<body>

<h2>🔎 OSINT Multi-Engine Search</h2>

<form method="POST">
    <input id="query" name="query" placeholder="Enter search query..." style="width:400px;" required>
    <br>
    <button type="submit">Search</button>
</form>

<div class="box">
<h3>🔎 Core DuckDuckGo Dorks</h3>

<b>Site-specific</b>
<span class="dork" onclick='setQuery("site:example.com password")'>site:example.com password</span>

<b>File types</b>
<span class="dork" onclick='setQuery("filetype:pdf confidential")'>filetype:pdf "confidential"</span>
<span class="dork" onclick='setQuery("filetype:xls email list")'>filetype:xls "email list"</span>

<b>Exact match</b>
<span class="dork" onclick='setQuery("\\"internal use only\\"")'>"internal use only"</span>

<b>Exclude terms</b>
<span class="dork" onclick='setQuery("admin panel -demo -test")'>admin panel -demo -test</span>

<b>URL search</b>
<span class="dork" onclick='setQuery("inurl:login")'>inurl:login</span>
<span class="dork" onclick='setQuery("inurl:admin")'>inurl:admin</span>

<b>Title search</b>
<span class="dork" onclick='setQuery("intitle:index of")'>intitle:"index of"</span>
</div>

<div class="box">
<h3>⚡ Common Dorks</h3>

<b>📂 Open directories</b>
<span class="dork" onclick='setQuery("intitle:index of backup")'>intitle:"index of" "backup"</span>
<span class="dork" onclick='setQuery("intitle:index of database.sql")'>intitle:"index of" "database.sql"</span>

<b>🔐 Login panels</b>
<span class="dork" onclick='setQuery("inurl:login site:example.com")'>inurl:login site:example.com</span>
<span class="dork" onclick='setQuery("inurl:admin panel")'>inurl:admin panel</span>

<b>📄 Sensitive files</b>
<span class="dork" onclick='setQuery("filetype:env DB_PASSWORD")'>filetype:env DB_PASSWORD</span>
<span class="dork" onclick='setQuery("filetype:log error")'>filetype:log "error"</span>
<span class="dork" onclick='setQuery("filetype:sql dump")'>filetype:sql "dump"</span>

<b>📧 Emails</b>
<span class="dork" onclick='setQuery("@gmail.com site:example.com")'>"@gmail.com" site:example.com</span>

<b>🧠 API keys</b>
<span class="dork" onclick='setQuery("api_key filetype:json")'>"api_key" filetype:json</span>
<span class="dork" onclick='setQuery("authorization bearer")'>"authorization: bearer"</span>
</div>

<div class="box">
<h3>🧠 Query Builder</h3>
<button onclick='appendQuery("site:")' type="button">+ site:</button>
<button onclick='appendQuery("filetype:")' type="button">+ filetype:</button>
<button onclick='appendQuery("inurl:")' type="button">+ inurl:</button>
<button onclick='appendQuery("intitle:")' type="button">+ intitle:</button>
<button onclick='appendQuery("\\" \\"")' type="button">+ ""</button>
<button onclick='appendQuery("-")' type="button">+ exclude (-)</button>
</div>

{% if results %}
<div class="result">
    <h3>Extracted Names:</h3>
    <ul>
    {% for name in names %}
        <li>{{ name }}</li>
    {% endfor %}
    </ul>

    <h3>Results:</h3>
    {% for r in results %}
        <p>
            <b>{{ r.title }}</b> ({{ r.source }})<br>
            {{ r.snippet }}
        </p>
    {% endfor %}
</div>
{% endif %}

</body>
</html>
"""


# --- DuckDuckGo ---
def search_ddg(query, max_results=10):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title"),
                "snippet": r.get("body"),
                "source": "DuckDuckGo"
            })
    return results


# --- Bing API ---
def search_bing(query, max_results=10):
    if not BING_API_KEY:
        return []

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": max_results}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    results = []
    if "webPages" in data:
        for item in data["webPages"]["value"]:
            results.append({
                "title": item.get("name"),
                "snippet": item.get("snippet"),
                "source": "Bing"
            })

    return results


# --- Combine results ---
def search_all(query):
    results = []

    results.extend(search_ddg(query))
    results.extend(search_bing(query))

    # Deduplicate by title
    seen = set()
    unique_results = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique_results.append(r)

    return unique_results


def extract_names(text):
    doc = nlp(text)
    names = set()

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.add(ent.text)

    return list(names)


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    names = []

    if request.method == "POST":
        query = request.form["query"]

        results = search_all(query)

        combined_text = " ".join([r["title"] + " " + r["snippet"] for r in results])
        names = extract_names(combined_text)

    return render_template_string(HTML, results=results, names=names)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Running on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)