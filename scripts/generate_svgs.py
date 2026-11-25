import os
import sys
import requests

USERNAME = "VigneshHegde78"
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    print("Error: GITHUB_TOKEN is missing")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
          }
        }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME}},
    headers=HEADERS,
).json()

if "errors" in response or not response.get("data", {}).get("user"):
    print("GitHub API Error:", response)
    sys.exit(1)

res = response["data"]["user"]

# Ensure assets directory exists on the runner
os.makedirs("assets", exist_ok=True)

# --- 1. GENERATE COMMITS BAR CHART (assets/commits.svg) ---
cal = res["contributionsCollection"]["contributionCalendar"]
total_commits = cal["totalContributions"]
weekly_counts = [
    sum(d["contributionCount"] for d in w["contributionDays"])
    for w in cal["weeks"]
]
max_week = max(weekly_counts) if weekly_counts else 1

bars_svg = []
bar_w, gap, max_h = 10, 4, 80
for i, count in enumerate(weekly_counts):
    h = max(4, int((count / max_week) * max_h)) if max_week > 0 else 4
    y = max_h - h + 10
    x = i * (bar_w + gap)
    ratio = count / max_week if max_week > 0 else 0
    color = "#39d353" if ratio > 0.7 else "#26a641" if ratio > 0.35 else "#0e4429" if count > 0 else "#161b22"
    bars_svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="2" fill="{color}" />')

width = len(weekly_counts) * (bar_w + gap)
commits_svg = f"""<svg width="{width}" height="125" viewBox="0 0 {width} 125" xmlns="http://www.w3.org/2000/svg">
  {''.join(bars_svg)}
  <text x="0" y="112" fill="#8b949e" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">
    {total_commits:,} contributions in the last year · busiest week {max_week}
  </text>
</svg>"""

with open("assets/commits.svg", "w") as f:
    f.write(commits_svg)

# --- 2. GENERATE LANGUAGE BAR (assets/tools.svg) ---
lang_totals = {}
lang_colors = {}
for repo in res["repositories"]["nodes"]: