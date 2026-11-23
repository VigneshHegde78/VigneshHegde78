import datetime
import html
import json
import os
import urllib.request

# --- USER CONFIGURATION ---
USERNAME = os.environ.get("GITHUB_ACTOR", "VigneshHegde78")
TOKEN = os.environ.get("ACCESS_TOKEN", "")
BIRTHDAY = datetime.date(2005, 10, 20)
ASCII_FILE = "ascii.txt"
OUTPUT_SVG = "dark_mode.svg"

# Right-hand profile sections (key, value)
# Set key to None for section headers
SECTIONS = [
    (None, f"{USERNAME}@fedora"),
    ("OS", "Fedora Linux, Android"),
    ("Uptime", "{uptime}"),
    ("Host", "Love for Code"),
    ("Kernel", "Software Developer"),
    ("IDE", "Ghostty, VS Code"),
    ("", ""),
    ("Languages.Programming", "JavaScript, TypeScript, Python, Dart"),
    ("Languages.Frameworks", "React, Next.js, React Native, Flutter"),
    ("Languages.Real", "English, Hindi, Marathi"),
    ("", ""),
    ("Hobbies.Software", "Linux Ricing, Open Source, AI Tools"),
    ("Hobbies.Hardware", "Custom Setups, Fitness"),
    ("", ""),
    (None, "- Contact --"),
    ("GitHub", f"github.com/{USERNAME}"),
    ("Email.Personal", "your-email@example.com"),
    ("LinkedIn", "your-linkedin-handle"),
    ("", ""),
    (None, "- GitHub Stats --"),
]

# Total character width of the right-hand info column (used for dot-padding)
INFO_COL_WIDTH = 62


def calculate_uptime(bday: datetime.date) -> str:
    today = datetime.date.today()
    years = today.year - bday.year
    months = today.month - bday.month
    days = today.day - bday.day

    if days < 0:
        months -= 1
        prev_month = (today.month - 1) or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days_in_prev = (datetime.date(prev_year, prev_month % 12 + 1, 1) - datetime.timedelta(days=1)).day if prev_month < 12 else 31
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


def graphql_query(query: str, variables: dict) -> dict:
    if not TOKEN:
        return {}
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Neofetch-Profile-Generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_github_stats() -> dict:
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes {
            stargazerCount
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 100) {
                    nodes {
                      additions
                      deletions
                      author { user { login } }
                    }
                  }
                }
              }
            }
          }
        }
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {
          totalCount
        }
      }
    }
    """
    data = graphql_query(query, {"login": USERNAME}).get("data", {}).get("user", {})
    if not data:
        return {"repos": 0, "contributed": 0, "stars": 0, "commits": 0, "followers": 0, "loc": 0, "add": 0, "del": 0}

    repos = data["repositories"]["totalCount"]
    contributed = data["repositoriesContributedTo"]["totalCount"]
    followers = data["followers"]["totalCount"]
    contrib = data["contributionsCollection"]
    commits = contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"]

    stars = 0
    additions = 0
    deletions = 0

    for repo in data["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        branch = repo.get("defaultBranchRef")
        if branch and branch.get("target"):
            for commit in branch["target"]["history"]["nodes"]:
                author_user = (commit.get("author") or {}).get("user")
                if author_user and author_user.get("login", "").lower() == USERNAME.lower():
                    additions += commit.get("additions", 0)
                    deletions += commit.get("deletions", 0)

    return {
        "repos": repos,
        "contributed": contributed,
        "stars": stars,
        "commits": commits,
        "followers": followers,
        "loc": additions - deletions,
        "add": additions,
        "del": deletions,
    }


def format_kv_svg(key: str, val: str, total_width: int) -> str:
    dots_count = max(2, total_width - len(key) - len(val) - 2)
    dots = "." * dots_count
    return (
        f'<tspan class="key">.{html.escape(key)}</tspan>'
        f'<tspan class="dots">:{dots}:</tspan>'
        f'<tspan class="val">{html.escape(val)}</tspan>'
    )


def build_right_lines(stats: dict) -> list[str]:
    uptime = calculate_uptime(BIRTHDAY)
    lines = []

    for key, raw_val in SECTIONS:
        val = raw_val.format(uptime=uptime)
        if key is None:
            # Section header
            dashes = "-" * max(2, INFO_COL_WIDTH - len(val) - 1)
            lines.append(f'<tspan class="header">{html.escape(val)} {dashes}</tspan>')
        elif key == "" and val == "":
            lines.append("")
        else:
            lines.append(format_kv_svg(key, val, INFO_COL_WIDTH))

    # Stats block (matches reference screenshot layout)
    r_left = f".Repos:....{stats['repos']} {{Contributed: {stats['contributed']}}}"
    r_right = f"Stars:........{stats['stars']}"
    pad1 = " " * max(1, (INFO_COL_WIDTH - len(r_left) - len(r_right) - 3) // 2)
    lines.append(
        f'<tspan class="key">.Repos</tspan><tspan class="dots">:....</tspan>'
        f'<tspan class="val">{stats["repos"]} {{Contributed: {stats["contributed"]}}}</tspan>'
        f'<tspan class="dots">{pad1} | {pad1}</tspan>'
        f'<tspan class="key">Stars</tspan><tspan class="dots">:........</tspan>'
        f'<tspan class="val">{stats["stars"]}</tspan>'
    )

    c_left = f".Commits:..........{stats['commits']}"
    c_right = f"Followers:.......{stats['followers']}"
    pad2 = " " * max(1, (INFO_COL_WIDTH - len(c_left) - len(c_right) - 3) // 2)
    lines.append(
        f'<tspan class="key">.Commits</tspan><tspan class="dots">:..........</tspan>'
        f'<tspan class="val">{stats["commits"]}</tspan>'
        f'<tspan class="dots">{pad2} | {pad2}</tspan>'
        f'<tspan class="key">Followers</tspan><tspan class="dots">:.......</tspan>'
        f'<tspan class="val">{stats["followers"]}</tspan>'
    )

    loc_str = f"{stats['loc']:,}"
    add_str = f"{stats['add']:,}++"
    del_str = f"{stats['del']:,}--"
    lines.append(
        f'<tspan class="key">.Lines of Code on GitHub</tspan><tspan class="dots">:.</tspan>'
        f'<tspan class="val">{loc_str} ( </tspan>'
        f'<tspan class="add">{add_str}</tspan><tspan class="val">, </tspan>'
        f'<tspan class="del">{del_str}</tspan><tspan class="val"> )</tspan>'
    )

    return lines


def generate_svg():
    with open(ASCII_FILE, "r", encoding="utf-8") as f:
        ascii_lines = [line.rstrip("\r\n") for line in f.readlines()]

    ascii_width = max((len(line) for line in ascii_lines), default=50)
    padded_ascii = [line.ljust(ascii_width) for line in ascii_lines]

    stats = fetch_github_stats()
    right_lines = build_right_lines(stats)

    total_rows = max(len(padded_ascii), len(right_lines))
    line_height = 20
    height = total_rows * line_height + 40
    width = (ascii_width + INFO_COL_WIDTH + 6) * 8.6

    tspans = []
    for i in range(total_rows):
        y = 28 + i * line_height
        left_txt = html.escape(padded_ascii[i]) if i < len(padded_ascii) else " " * ascii_width
        right_svg = right_lines[i] if i < len(right_lines) else ""
        tspans.append(
            f'<text x="20" y="{y}" xml:space="preserve">'
            f'<tspan class="ascii">{left_txt}</tspan>   {right_svg}'
            f"</text>"
        )

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{height}" viewBox="0 0 {int(width)} {height}">
  <style>
    svg {{
      background-color: #161b22;
      font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
      font-size: 14px;
    }}
    .ascii {{ fill: #c9d1d9; }}
    .header {{ fill: #58a6ff; font-weight: bold; }}
    .key {{ fill: #ffa657; }}
    .dots {{ fill: #484f58; }}
    .val {{ fill: #c9d1d9; }}
    .add {{ fill: #3fb950; }}
    .del {{ fill: #f85149; }}
  </style>
  {"".join(tspans)}
</svg>
"""
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)


if __name__ == "__main__":
    generate_svg()