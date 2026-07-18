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

    # Metrics logic
    professions = ["tutor", "teacher", "doctor", "lawyer", "engineer", "scientist", "programmer", "expert", "professor"]
    if any(prof in lowered for prof in professions):
        score += 20
        metrics_passed.append("Persona Validation: Met (+20)")
    
    question_starters = ["what", "how", "why", "can", "could"]
    if prompt.endswith("?") or any(lowered.startswith(s) for s in question_starters):
        score += 40
        metrics_passed.append("Inquiry Structure: Met (+40)")

    action_keywords = ["explain", "summarize", "analyze", "simplify", "debug", "format", "list"]
    found_keywords = [kw for kw in action_keywords if kw in lowered]
    req = 5 if st.session_state.selected_level in ["advanced", "professor"] else 3
    if len(found_keywords) >= req:
        score += 20
        metrics_passed.append(f"Command Density: {len(found_keywords)}/{req} (+20)")

    score += word_count
    metrics_passed.append(f"Linguistic Expansion: +{word_count}")

    # Universal 100-point cap
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
    ax.grid(True, color='#2c3d47', linestyle='--')
    st.pyplot(fig)

# --- EDUCATIONAL TOPIC DATA ---
TOPICS = {
    "beginner": {
        "keywords": {"title": "How to use keywords", "desc": "Keywords act as signposts for AI systems. By incorporating precise descriptive terms, you minimize ambiguity.", "url": "https://www.searchenginejournal.com/keyword-research/"},
        "why_ai": {"title": "Why should I use AI", "desc": "AI handles repetitive tasks, debugs code, and structures complex data as a massive productivity multiplier.", "url": "https://www.ibm.com/topics/artificial-intelligence"},
        "how_ai_works": {"title": "How does AI work", "desc": "Modern AI relies on Neural Networks and Machine Learning to recognize text patterns and predict outputs.", "url": "https://www.bbc.com/news/technology-65824143"}
    },
    "advanced": {
        "how_use_ai": {"title": "How should I use AI", "desc": "Advanced users focus on integration parameters: engineering targeted system prompts and chain-of-thought pathways.", "url": "https://www.zdnet.com/article/how-to-use-chatgpt/"},
        "pros_cons_ai": {"title": "Pros and cons of AI", "desc": "Pros: Extreme cognitive acceleration. Cons: Hallucination risks and structural dataset bias.", "url": "https://www.forbes.com/sites/bernardmarr/2023/06/02/the-pros-and-cons-of-artificial-intelligence-everyone-should-know/"},
        "what_llms": {"title": "What are LLMs", "desc": "LLMs are deep learning algorithms trained on billions of parameters using transformer token layouts.", "url": "https://www.cloudflare.com/learning/ai/what-is-large-language-model/"}
    },
    "professor": {
        "ai_literacy_stats": {"title": "How many people are AI literate", "desc": "Global assessments show basic usage is widespread, but deep algorithmic literacy remains below 25%.", "url": "https://www.unesco.org/en/articles/ai-competency-frameworks-school-students-and-teachers"},
        "class_disparities": {"title": "Socio-economic class disparities", "desc": "The 'AI Divide' shadows financial wealth, giving early tool access primarily to well-funded areas.", "url": "https://www.worldbank.org/en/topic/digital-development/overview"},
        "tech_behind_countries": {"title": "Countries furthest behind in tech", "desc": "Developing nations face power grid instability and lack of infrastructure, limiting cloud engine use.", "url": "https://www.un.org/en/un75/impact-digital-technologies"}
    },
    "true master": {
        "grow_business": {"title": "How to use AI to grow your business", "desc": "Deploy AI for automating customer pipelines, predictive financial analysis, and scaling marketing production dynamically.", "url": "https://www.hbr.org/"},
        "agentic_systems": {"title": "What are Agentic Architecture & Autonomous Systems", "desc": "Move beyond chatbots. Agentic AI designs independent loops where software sets goals, executes actions, and reviews outcomes self-sufficiently.", "url": "https://www.gartner.com/"},
        "knowledge_seo": {"title": "How to use your knowledge SEO", "desc": "Optimize your intellectual content for AI search index summaries, large language model ingestion pipelines, and semantic web visibility.", "url": "https://www.searchengineland.com/"},
        "ai_governance": {"title": "How to understand AI Governance, Alignment, & Safety Engineering", "desc": "Examine code boundary conditions, model bias control layers, ethical alignment parameters, and compliance standards.", "url": "https://www.openai.com/safety/"},
        "tie_off": {"title": "How to tie all this knowledge off", "desc": "Unify your foundational, engineering, macro-economic, and organizational workflows into an integrated action strategy.", "url": "https://github.com/"}
    }
}

# --- WEB APP NAVIGATION & LAYOUT ---
st.set_page_config(page_title="Professor AI | Mastery Platform", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #7FFFD4; color: #111E25; }
    h1, h2, h3 { color: #111E25 !important; font-family: 'Helvetica Neue', sans-serif; }
    .hero-text { font-size: 1.2rem; line-height: 1.6; color: #1c2d37; margin-bottom: 25px; }
    .feature-box { background-color: rgba(17, 30, 37, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #111E25; }
    div.stButton > button { background-color: #111E25; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 50px; }
    </style>
""", unsafe_allow_html=True)

# Navigation Router
if st.session_state.current_page == "Home":
    st.title("🤖 PROFESSOR AI")
    st.subheader("Master the Art of Algorithmic Command")
    
    st.markdown("""
    <div class="hero-text">
    Professor AI is a strategic educational ecosystem built to transform how humans interact with Artificial Intelligence. 
    Our curriculum bridges the gap between basic chat interactions and professional-grade engineering. Whether you are 
    automating a business or exploring the ethics of AI governance, our platform provides the tools to dominate 
    the digital frontier.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("### 🚀 Why Choose Professor AI?")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="feature-box">
        <strong>⚡ Real-Time Prompt Grading</strong><br>
        Stop guessing. Our proprietary Analytics Engine evaluates your prompts based on Persona, Inquiry Depth, and Command Density.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
        <strong>🏆 Segmented Scoreboards</strong><br>
        Benchmark your progress. Compete in isolated leaderboards for Beginner, Advanced, and Professor-level tracks.
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    if st.button("ENTER THE LAB ➔"):
        st.session_state.current_page = "User Setup"
        st.rerun()

elif st.session_state.current_page == "User Setup":
    st.title("Register Profile")
    username = st.text_input("Enter your username:", value=st.session_state.username)
    if st.button("Submit"):
        if username.strip() == "":
            st.warning("Please enter a username!")
        else:
            st.session_state.username = username.strip()
            st.session_state.current_page = "Dashboard"
            st.rerun()
    if st.button("Back Home"):
        st.session_state.current_page = "Home"
        st.rerun()

elif st.session_state.current_page == "Dashboard":
    st.title("🎓 Dashboard")
    st.write(f"Logged in as: **{st.session_state.username}**")
    if st.button("Create a New Chat"):
        st.session_state.current_page = "Difficulty"
        st.rerun()
    if st.button("Logout / Back"):
        st.session_state.current_page = "User Setup"
        st.rerun()

elif st.session_state.current_page == "Difficulty":
    st.title("Select Your Difficulty Level")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Beginner", use_container_width=True):
            st.session_state.selected_level = "beginner"
            st.session_state.current_page = "Syllabus"
            st.rerun()
    with col2:
        if st.button("Advanced", use_container_width=True):
            st.session_state.selected_level = "advanced"
            st.session_state.current_page = "Syllabus"
            st.rerun()
    with col3:
        if st.button("Professor Level", use_container_width=True):
            st.session_state.selected_level = "professor"
            st.session_state.current_page = "Syllabus"
            st.rerun()
    with col4:
        if st.button("True Master 👑", use_container_width=True):
            st.session_state.selected_level = "true master"
            st.session_state.master_confirmed = False
            st.session_state.current_page = "Master Gate"
            st.rerun()

elif st.session_state.current_page == "Master Gate":
    st.title("👑 True Master Verification")
    st.subheader("Do you want to actually learn AI?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, I am ready.", use_container_width=True):
            st.session_state.master_confirmed = True
            save_score_to_disk(st.session_state.username or "Anonymous", "Accessed Master Course", 0, "true master")
            st.session_state.current_page = "Syllabus"
            st.rerun()
    with col2:
        if st.button("No, take me back.", use_container_width=True):
            st.session_state.current_page = "Difficulty"
            st.rerun()

elif st.session_state.current_page == "Syllabus":
    st.title("Dynamic Learning Portal")
    st.subheader(f"Track: {st.session_state.selected_level.upper()}")
    level_data = TOPICS[st.session_state.selected_level]
    
    if st.session_state.selected_level == "true master":
        for index, (key, data) in enumerate(level_data.items()):
            if st.button(data["title"], key=f"btn_{key}", use_container_width=True):
                st.session_state.selected_topic = data
    else:
        cols = st.columns(3)
        for index, (key, data) in enumerate(level_data.items()):
            with cols[index]:
                if st.button(data["title"], key=f"btn_{key}", use_container_width=True):
                    st.session_state.selected_topic = data

    if st.session_state.selected_topic:
        st.info(st.session_state.selected_topic["desc"])
        st.markdown(f"[🔗 Lesson Resources]({st.session_state.selected_topic['url']})")

    st.write("---")
    if st.session_state.selected_level == "true master":
        if st.button("↩ Exit to Main Menu"):
            st.session_state.current_page = "Home"
            st.rerun()
    else:
        if st.button("Proceed to Analytics Test ➔"):
            st.session_state.current_try = 1
            st.session_state.user_scores = []
            st.session_state.current_page = "Test Lab"
            st.rerun()

elif st.session_state.current_page == "Test Lab":
    st.title("🧪 Prompt Assessment Engine Lab")
    st.write(f"**Current Tracker**: Attempt {st.session_state.current_try} / 3")
    user_prompt = st.text_input("Type your test query here:", key="prompt_entry_box")
    
    if st.button("Evaluate Performance", disabled=(st.session_state.current_try > 3)):
        if user_prompt.strip() == "":
            st.error("Please type a prompt first!")
        else:
            score, breakdown = evaluate_prompt_string(user_prompt)
            st.session_state.user_scores.append(score)
            save_score_to_disk(st.session_state.username or "Anonymous", user_prompt, score, st.session_state.selected_level)
            st.success(f"Final Score: {score}/100 | " + " | ".join(breakdown[:2]))
            st.session_state.current_try += 1
                
    if len(st.session_state.user_scores) > 0:
        render_analytics_graph()
        
    if st.button("↩ Back to Menu"):
        st.session_state.current_page = "Home"
        st.rerun()

# --- ADMIN VIEW ---
st.write("---")
st.subheader("📋 SEGMENTED SCOREBOARDS (Admin View)")
selected_board = st.selectbox("View Scoreboard Track:", options=["Beginner Track Logs", "Advanced Track Logs", "Professor Track Logs", "True Master Premium Logs"])
board_mapping = {"Beginner Track Logs": "beginner", "Advanced Track Logs": "advanced", "Professor Track Logs": "professor", "True Master Premium Logs": "true master"}
target_file_name = SCOREBOARD_FILES[board_mapping[selected_board]]

if os.path.exists(target_file_name):
    with open(target_file_name, "r", encoding="utf-8") as file:
        log_data = file.read()
    st.text_area(f"Raw Logs [{target_file_name}]:", value=log_data, height=150)
else:
    st.info("No records recorded for this track yet.")
