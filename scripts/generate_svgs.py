import os
import requests

USERNAME = "VigneshHegde78"
TOKEN = os.environ["GITHUB_TOKEN"]

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

res = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME}},
    headers=HEADERS,
).json()["data"]["user"]

# --- 1. GENERATE COMMITS BAR CHART (commits.svg) ---
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
    # Color intensity based on weekly volume
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

with open("commits.svg", "w") as f:
    f.write(commits_svg)

# --- 2. GENERATE LANGUAGE BAR (tools.svg) ---
lang_totals = {}
lang_colors = {}
for repo in res["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        lang_totals[name] = lang_totals.get(name, 0) + edge["size"]
        lang_colors[name] = edge["node"]["color"] or "#8b949e"

total_bytes = sum(lang_totals.values()) or 1
top_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:5]

segments_svg = []
legend_svg = []
curr_x = 0
bar_total_w = 720
seg_gap = 4

for idx, (name, size) in enumerate(top_langs):
    pct = (size / total_bytes) * 100
    seg_w = max(8, int((size / total_bytes) * (bar_total_w - seg_gap * (len(top_langs) - 1))))
    color = lang_colors[name]
    segments_svg.append(f'<rect x="{curr_x}" y="10" width="{seg_w}" height="8" rx="4" fill="{color}" />')
    curr_x += seg_w + seg_gap

    lx = idx * 145
    legend_svg.append(
        f'<circle cx="{lx + 5}" cy="40" r="4.5" fill="{color}" />'
        f'<text x="{lx + 15}" y="44" fill="#c9d1d9" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">{name} {round(pct)}%</text>'
    )

tools_svg = f"""<svg width="730" height="60" viewBox="0 0 730 60" xmlns="http://www.w3.org/2000/svg">
  {''.join(segments_svg)}
  {''.join(legend_svg)}
</svg>"""

with open("tools.svg", "w") as f:
    f.write(tools_svg)