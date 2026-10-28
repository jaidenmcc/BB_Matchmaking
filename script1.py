import json
import os
import numpy as np
import openpyxl
import pandas as pd

# 1. Load Excel file
file_path = "/Users/jaidenmccully/PycharmProjects/Brain Buddies Matchmaking/Brain Buddies Mentee-Mentor Matching Form(1-57).xlsx"

if not os.path.exists(file_path):
    print(f"Error: Could not find '{file_path}'.")
    exit()

print(f"Loading responses from '{file_path}'...")
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip()

# 2. Dynamic column detection
role_col = [c for c in df.columns if "Would you like to be a mentor or mentee" in c][0]
name_col = "What is your Name?"
program_col = "Are you a Psychology Student or a Neuroscience Student?"
year_col = [c for c in df.columns if "What year are you in" in c][0]
freq_col = "How often would you like to meet with your mentor/mentee in person?"
interests_col = [c for c in df.columns if "specific interests" in c][0]

mentor_courses_col = [c for c in df.columns if "comfortable helping your mentee" in c][0]
multi_mentee_col = [c for c in df.columns if "more than one mentee" in c][0]
mentee_courses_col = [c for c in df.columns if "like help with?" in c][0]
special_req_col = [c for c in df.columns if "special requests" in c][0]

# Separate Mentors and Mentees
mentors = df[df[role_col].str.contains("Mentor", case=False, na=False)].copy().reset_index(drop=True)
mentees = df[df[role_col].str.contains("Mentee", case=False, na=False)].copy().reset_index(drop=True)

print(f"Loaded {len(mentors)} Mentors and {len(mentees)} Mentees.")


# 3. Detailed Scoring Breakdown Logic
def calculate_match_breakdown(mentor, mentee):
    p_score = 0.20 if mentor[program_col] == mentee[program_col] else 0.0
    f_score = 0.30 if mentor[freq_col] == mentee[freq_col] else 0.0

    c_score = 0.0
    m_courses = str(mentor[mentor_courses_col]).lower()
    e_courses = str(mentee[mentee_courses_col]).lower()
    if e_courses not in ["nan", "n/a"]:
        if "all core" in m_courses or e_courses in m_courses or any(
                code in m_courses for code in e_courses.replace("/", ",").split(",") if len(code.strip()) > 3):
            c_score = 0.40

    m_interests = set(str(mentor[interests_col]).lower().split())
    e_interests = set(str(mentee[interests_col]).lower().split())
    stop_words = {"and", "in", "of", "or", "a", "to", "is"}
    common_words = m_interests.intersection(e_interests) - stop_words
    i_score = 0.10 if len(common_words) > 0 else 0.0

    total = round(p_score + f_score + c_score + i_score, 2)
    return total, p_score, f_score, c_score, i_score


# Build Matrix & Data Payloads for Frontend JS
matrix_data = []
for _, mentee in mentees.iterrows():
    row_data = {
        "mentee": str(mentee[name_col]),
        "program": str(mentee[program_col]) if program_col in mentee else "N/A",
        "scores": {},
        "breakdowns": {}
    }
    for _, mentor in mentors.iterrows():
        total, p_s, f_s, c_s, i_s = calculate_match_breakdown(mentor, mentee)
        m_name = str(mentor[name_col])
        row_data["scores"][m_name] = total
        row_data["breakdowns"][m_name] = {"program": p_s, "freq": f_s, "courses": c_s, "interests": i_s}
    matrix_data.append(row_data)

dashboard_payload = {
    "mentors": [str(m) for m in mentors[name_col]],
    "mentees": [str(m) for m in mentees[name_col]],
    "matrix": matrix_data
}

with open("match_data.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_payload, f, indent=2)

# 4. Generate the Ultimate Interactive Landing Page HTML
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Brain Buddies Matchmaking Landing Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="bg-slate-50 text-slate-800 font-sans antialiased min-h-screen">

    <!-- Top Navigation / Header -->
    <header class="bg-indigo-900 text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-6 py-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <span class="bg-indigo-700 text-indigo-200 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">Official Matchmaking Portal</span>
                <h1 class="text-3xl font-extrabold tracking-tight mt-2">Brain Buddies Dashboard</h1>
                <p class="text-indigo-200 mt-1">Algorithmic Mentor & Mentee Pairing System</p>
            </div>
            <div class="flex items-center gap-4 bg-indigo-800/60 p-4 rounded-xl border border-indigo-700">
                <div class="text-center px-4 border-r border-indigo-700">
                    <span class="block text-2xl font-bold text-white">{len(mentees)}</span>
                    <span class="text-xs text-indigo-300">Mentees</span>
                </div>
                <div class="text-center px-4">
                    <span class="block text-2xl font-bold text-white">{len(mentors)}</span>
                    <span class="text-xs text-indigo-300">Mentors</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <main class="max-w-7xl mx-auto px-6 py-8">

        <!-- Controls & Search Bar -->
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-8 flex flex-col lg:flex-row justify-between items-center gap-4">
            <div class="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                <button onclick="switchView('cards')" id="btn-cards" class="px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-indigo-600 text-white shadow-sm">Card Inspector</button>
                <button onclick="switchView('matrix')" id="btn-matrix" class="px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-slate-100 text-slate-600 hover:bg-slate-200">Full Matrix Grid</button>
            </div>
            <div class="w-full lg:w-80 relative">
                <input type="text" id="searchInput" placeholder="Search by Mentee Name..." 
                    class="w-full px-4 py-2.5 pl-10 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition" 
                    onkeyup="filterDashboard()">
                <span class="absolute left-3.5 top-3 text-slate-400">🔍</span>
            </div>
        </div>

        <!-- View 1: Card Inspector (Interactive Grid) -->
        <div id="view-cards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
"""

# Render Interactive Cards for each Mentee
for row in matrix_data:
    mentee_name = row["mentee"]
    sorted_matches = sorted(row["scores"].items(), key=lambda x: x[1], reverse=True)

    html_content += f"""
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between hover:shadow-md transition mentee-item" data-name="{mentee_name.lower()}">
                <div>
                    <div class="flex justify-between items-start mb-3">
                        <h3 class="text-lg font-bold text-slate-900">{mentee_name}</h3>
                        <span class="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2.5 py-1 rounded-lg">Mentee</span>
                    </div>
                    <p class="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Top Recommended Mentors</p>
                    <div class="space-y-2 mb-4">
"""
    for m_name, score in sorted_matches[:3]:
        badge_bg = "bg-emerald-50 text-emerald-700 border-emerald-200" if score >= 0.5 else "bg-amber-50 text-amber-700 border-amber-200" if score >= 0.3 else "bg-slate-50 text-slate-600 border-slate-200"
        html_content += f"""
                        <div class="flex justify-between items-center text-sm p-2.5 bg-slate-50/70 rounded-xl border border-slate-100">
                            <span class="font-medium text-slate-700 truncate max-w-[180px]">{m_name}</span>
                            <span class="px-2 py-0.5 rounded-lg text-xs font-bold border {badge_bg}">{int(score * 100)}% match</span>
                        </div>
"""
    html_content += f"""
                    </div>
                </div>
                <button onclick="openBreakdownModal('{mentee_name}')" class="w-full mt-2 py-2.5 bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-600 font-semibold text-sm rounded-xl transition">
                    View Full Score Breakdown
                </button>
            </div>
"""

html_content += f"""
        </div>

        <!-- View 2: Full Matrix Grid (Hidden by default) -->
        <div id="view-matrix" class="hidden bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="p-6 overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 text-sm text-left">
                    <thead class="bg-slate-50">
                        <tr>
                            <th class="px-4 py-3 font-bold text-slate-700 sticky left-0 bg-slate-50 z-10">Mentee Name</th>
"""
for m_name in dashboard_payload["mentors"]:
    html_content += f"""                            <th class="px-4 py-3 font-semibold text-slate-600 text-center whitespace-nowrap">{m_name}</th>\n"""

html_content += f"""
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 bg-white">
"""

for row in matrix_data:
    html_content += f"""                        <tr class="hover:bg-slate-50/80 matrix-row" data-name="{row['mentee'].lower()}">
                            <td class="px-4 py-3 font-medium text-slate-900 sticky left-0 bg-white z-10">{row['mentee']}</td>\n"""
    for m_name in dashboard_payload["mentors"]:
        score = row["scores"].get(m_name, 0.0)
        color_class = "text-emerald-700 bg-emerald-50 font-bold" if score >= 0.5 else "text-amber-700 bg-amber-50" if score >= 0.3 else "text-slate-400"
        html_content += f"""                            <td class="px-4 py-3 text-center {color_class}">{score}</td>\n"""
    html_content += f"""                        </tr>\n"""

html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <!-- Detailed Modal for Score Breakdown -->
    <div id="breakdownModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
        <div class="bg-white w-full max-w-2xl rounded-3xl shadow-2xl p-6 md:p-8 relative">
            <button onclick="closeModal()" class="absolute top-6 right-6 text-slate-400 hover:text-slate-600 text-xl font-bold">&times;</button>
            <h2 id="modalTitle" class="text-2xl font-bold text-slate-900 mb-1">Match Breakdown</h2>
            <p class="text-sm text-slate-500 mb-6">Detailed algorithmic weights breakdown for this selection.</p>
            <div id="modalContent" class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                <!-- Injected via JavaScript -->
            </div>
            <div class="mt-8 pt-4 border-t border-slate-100 flex justify-end">
                <button onclick="closeModal()" class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl transition">Close</button>
            </div>
        </div>
    </div>

    <!-- Frontend Interactive Logic Script -->
    <script>
        const matchData = {json.dumps(dashboard_payload)};

        function switchView(view) {{
            const cardsView = document.getElementById('view-cards');
            const matrixView = document.getElementById('view-matrix');
            const btnCards = document.getElementById('btn-cards');
            const btnMatrix = document.getElementById('btn-matrix');

            if (view === 'cards') {{
                cardsView.classList.remove('hidden');
                matrixView.classList.add('hidden');
                btnCards.className = "px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-indigo-600 text-white shadow-sm";
                btnMatrix.className = "px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-slate-100 text-slate-600 hover:bg-slate-200";
            }} else {{
                cardsView.classList.add('hidden');
                matrixView.classList.remove('hidden');
                btnMatrix.className = "px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-indigo-600 text-white shadow-sm";
                btnCards.className = "px-5 py-2.5 rounded-xl font-semibold text-sm transition bg-slate-100 text-slate-600 hover:bg-slate-200";
            }}
        }}

        function filterDashboard() {{
            const query = document.getElementById('searchInput').value.toLowerCase();

            // Filter Cards
            const cards = document.getElementsByClassName('mentee-item');
            for (let card of cards) {{
                let name = card.getAttribute('data-name');
                card.style.display = name.includes(query) ? "" : "none";
            }}

            // Filter Matrix Rows
            const rows = document.getElementsByClassName('matrix-row');
            for (let row of rows) {{
                let name = row.getAttribute('data-name');
                row.style.display = name.includes(query) ? "" : "none";
            }}
        }}

        function openBreakdownModal(menteeName) {{
            const menteeObj = matchData.matrix.find(m => m.mentee === menteeName);
            if (!menteeObj) return;

            document.getElementById('modalTitle').innerText = `Matches for ${{menteeName}}`;
            const contentContainer = document.getElementById('modalContent');
            contentContainer.innerHTML = '';

            const sortedMentors = Object.entries(menteeObj.scores).sort((a, b) => b[1] - a[1]);

            sortedMentors.forEach(([mentorName, score]) => {{
                const breakdown = menteeObj.breakdowns[mentorName];
                const cardDiv = document.createElement('div');
                cardDiv.className = "p-4 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col gap-2";
                cardDiv.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-bold text-slate-800">${{mentorName}}</span>
                        <span class="px-2.5 py-1 rounded-lg text-xs font-extrabold bg-indigo-100 text-indigo-800">Total Score: ${{score}}</span>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-600 mt-1">
                        <div class="bg-white p-2 rounded-xl border border-slate-200">Program Match: <b class="text-slate-900">${{breakdown.program}}</b></div>
                        <div class="bg-white p-2 rounded-xl border border-slate-200">Frequency Match: <b class="text-slate-900">${{breakdown.freq}}</b></div>
                        <div class="bg-white p-2 rounded-xl border border-slate-200">Course Match: <b class="text-slate-900">${{breakdown.courses}}</b></div>
                        <div class="bg-white p-2 rounded-xl border border-slate-200">Interests Match: <b class="text-slate-900">${{breakdown.interests}}</b></div>
                    </div>
                `;
                contentContainer.appendChild(cardDiv);
            }});

            document.getElementById('breakdownModal').classList.remove('hidden');
            document.getElementById('breakdownModal').classList.add('flex');
        }}

        function closeModal() {{
            document.getElementById('breakdownModal').classList.remove('flex');
            document.getElementById('breakdownModal').classList.add('hidden');
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\nSUCCESS: Ultimate Interactive Landing Page generated with {len(mentees)}mentees and {len(mentors)} mentors!")