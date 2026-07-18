import streamlit as st
import matplotlib.pyplot as plt
import os

# --- LEVEL-SPECIFIC SCOREBOARD MAP ---
SCOREBOARD_FILES = {
    "beginner": "scores_beginner.txt",
    "advanced": "scores_advanced.txt",
    "professor": "scores_professor.txt",
    "true master": "scores_truemaster.txt"
}

# Initialize global variables
if "user_scores" not in st.session_state:
    st.session_state.user_scores = []
if "current_try" not in st.session_state:
    st.session_state.current_try = 1
if "selected_level" not in st.session_state:
    st.session_state.selected_level = "beginner"
if "username" not in st.session_state:
    st.session_state.username = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = None
if "master_confirmed" not in st.session_state:
    st.session_state.master_confirmed = False

def save_score_to_disk(username, prompt, score, level):
    target_file = SCOREBOARD_FILES.get(level, "scores_general.txt")
    try:
        with open(target_file, "a", encoding="utf-8") as file:
            if level == "true master":
                file.write(f"User: {username} | Action: {prompt}\n")
            else:
                file.write(f"User: {username} | Try: {st.session_state.current_try} | Score: {score} | Prompt: {prompt}\n")
    except Exception as e:
        st.error(f"Data Write Failure: {e}")

# --- PROMPT EVALUATION ENGINE ---
def evaluate_prompt_string(prompt):
    score = 0
    metrics_passed = []
    lowered = prompt.lower()
    word_count = len(prompt.split())

    if word_count == 0:
        return 0, ["❌ Empty query string flagged."]

    # 1. Role Persona Parameter (All levels benefit)
    professions = ["tutor", "teacher", "doctor", "lawyer", "engineer", "scientist", "programmer", "expert", "professor"]
    if any(prof in lowered for prof in professions):
        score += 20
        metrics_passed.append("Persona Validation: Met (+20)")
    else:
        metrics_passed.append("Missing explicit Persona constraints.")
    
    # 2. Inquiry Structure Parameter (All levels benefit)
    question_starters = ["what", "how", "why", "can", "could", "where", "who", "is", "are"]
    if prompt.endswith("?") or any(lowered.startswith(s) for s in question_starters):
        score += 40
        metrics_passed.append("Inquiry Structure: Met (+40)")
    else:
        metrics_passed.append("Missing structural interrogative formatting.")

    # 3. Level Keyword Challenge & Penalty Logic
    action_keywords = ["explain", "summarize", "analyze", "simplify", "debug", "format", "list", "bullet", "limit"]
    found_keywords = [kw for kw in action_keywords if kw in lowered]
    
    # Target scale shifts dynamically based on chosen path
    req = 5 if st.session_state.selected_level in ["advanced", "professor"] else 3
    
    if len(found_keywords) >= req:
        score += 20
        metrics_passed.append(f"Command Density: {len(found_keywords)}/{req} Met (+20)")
    else:
        score -= 10
        metrics_passed.append(f"❌ Command Density Failed: {len(found_keywords)}/{req} (-10 Penalty)")

    # 4. Word Count Scaling
    score += word_count
    metrics_passed.append(f"Linguistic Expansion: +{word_count} Points")

    # Safety clamp floor limits
    if score < 0:
        score = 0

    # Universal 100-point cap ceiling
    if score > 100:
        metrics_passed.append(f"⚠️ Limit: Score capped at 100 (Raw: {score})")
        score = 100

    return score, metrics_passed

# --- GRAPH RENDERER ---
def render_analytics_graph():
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor('#111E25')
    ax.set_facecolor('#1c2d37')
    attempts = [1, 2, 3]
    padded_scores = st.session_state.user_scores + [0] * (3 - len(st.session_state.user_scores))
    ax.plot(attempts, padded_scores, marker='o', color='#81C784', linewidth=2)
    ax.set_title(f"{st.session_state.selected_level.upper()} Performance Analytics", color='white', fontsize=10)
    ax.set_xticks(attempts)
    ax.set_ylim(0, 110)
