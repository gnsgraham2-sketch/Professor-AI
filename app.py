import streamlit as st
import matplotlib.pyplot as plt
import os
import re
from google import genai

# ==============================================================================
# 🔑 API KEY CONFIGURATION PLACEHOLDER
# You can paste your API key inside the quotes below, or enter it via the web app input field!
# ==============================================================================
HARDCODED_API_KEY = "AQ.Ab8RN6L772tqGW_KGm9oGn9dT0DpBKtEo6PwtK5NgUA9IStsHQ"  # <-- PASTE YOUR GEMINI API KEY HERE


# --- LEVEL-SPECIFIC SCOREBOARD MAP ---
SCOREBOARD_FILES = {
    "beginner": "scores_beginner.txt",
    "advanced": "scores_advanced.txt",
    "professor": "scores_professor.txt",
    "true master": "scores_truemaster.txt"
}

# Initialize global state variables
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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def save_score_to_disk(username, prompt, score, level):
    target_file = SCOREBOARD_FILES.get(level, "scores_general.txt")
    try:
        with open(target_file, "a", encoding="utf-8") as file:
            if level == "true master":
                file.write(f"User: {username} | Action: {prompt}\n")
            else:
                clean_prompt = prompt.replace('\n', ' ')
                file.write(f"User: {username} | Try: {st.session_state.current_try} | Score: {score} | Prompt: {clean_prompt}\n")
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

    # 1. Role Persona Parameter
    professions = ["tutor", "teacher", "doctor", "lawyer", "engineer", "scientist", "programmer", "expert", "professor"]
    if any(prof in lowered for prof in professions):
        score += 20
        metrics_passed.append("Persona Validation: Met (+20)")
    else:
        metrics_passed.append("Missing explicit Persona constraints.")
    
    # 2. Inquiry Structure Parameter
    question_starters = ["what", "how", "why", "can", "could", "where", "who", "is", "are"]
    if prompt.endswith("?") or any(lowered.startswith(s) for s in question_starters):
        score += 40
        metrics_passed.append("Inquiry Structure: Met (+40)")
    else:
        metrics_passed.append("Missing structural interrogative formatting.")

    # 3. Level Keyword Challenge & Penalty Logic
    action_keywords = ["explain", "summarize", "analyze", "simplify", "debug", "format", "list", "bullet", "limit"]
    found_keywords = [kw for kw in action_keywords if kw in lowered]
    
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

    if score < 0:
        score = 0

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
st.set_page_config(page_title="GramAI | Mastery Platform", page_icon="🤖", layout="centered")
ad_code = """
<script type="text/javascript">
    atOptions = {
        'key' : '2a0817139b81110a48b701f1166e493c',
        'format' : 'iframe',
        'height' : 300,
        'width' : 160,
        'params' : {}
    };
</script>
<script type="text/javascript" src="//highperformanceformat.com"></script>

# Set the height and width slightly larger than the ad to avoid scrollbars
components.html(ad_code, width=180, height=320)
st.markdown("""
<style>
    .stApp { background-color: #7FFFD4; color: #111E25; }
    h1, h2, h3 { color: #111E25 !important; font-family: 'Helvetica Neue', sans-serif; }
    .hero-text { font-size: 1.2rem; line-height: 1.6; color: #111E25; margin-bottom: 25px; }
    .feature-box { background-color: rgba(17, 30, 37, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #111E25; }
    div.stButton > button { background-color: #111E25; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 50px; }
    
    .white-score-text {
        color: #FFFFFF !important;
        background-color: #111E25;
        padding: 15px;
        border-radius: 8px;
        font-weight: 500;
        margin-top: 10px;
        margin-bottom: 15px;
        border-left: 5px solid #81C784;
    }
    </style>
""", unsafe_allow_html=True)

# Navigation Router
if st.session_state.current_page == "Home":
    st.title("🤖 GRAMAI")
    st.subheader("Master the Art of Algorithmic Command")
    
    st.markdown("""
    <div class="hero-text">
    GramAI is a strategic educational ecosystem built to transform how humans interact with Artificial Intelligence. 
    Our curriculum bridges the gap between basic chat interactions and professional-grade engineering. Whether you are 
    automating a business or exploring the ethics of AI governance, our platform provides the tools to dominate 
    the digital frontier.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("### 🚀 Why Choose GramAI?")
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

    if st.button("🤖 Chat with GramAI Assistant"):
        st.session_state.current_page = "Chatbot"
        st.rerun()

    if st.button("Logout / Back"):
        st.session_state.current_page = "User Setup"
        st.rerun()

elif st.session_state.current_page == "Chatbot":
    st.title("🤖 GramAI Evaluation Assistant")
    st.write("Submit any prompt to get an AI answer, a Professor Level score out of 100, and actionable feedback.")
    
    # Use hardcoded key if filled out, otherwise fall back to UI text entry
    if HARDCODED_API_KEY and HARDCODED_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        active_api_key = HARDCODED_API_KEY
    else:
        active_api_key = st.text_input("Enter your Gemini API Key:", type="password", key="gemini_api_key")
    
    if not active_api_key:
        st.info("🔑 Please paste your API key in `app.py` or enter it above to activate the evaluation assistant.")
    else:
        try:
            client = genai.Client(api_key=active_api_key)

            # Display chat message history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Accept new prompt input
            if user_input := st.chat_input("Type your prompt here for evaluation and response..."):
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})

                # ==============================================================================
                # 🎯 PROFESSOR LEVEL SCORING SYSTEM INSTRUCTION PROMPT
                # ==============================================================================
                system_evaluation_prompt = f"""
                You are GramAI Assistant, an expert prompt engineering evaluator and tutor.
                
                Analyze the user's prompt using the strictly defined PROFESSOR LEVEL scoring framework below:
                
                --- PROFESSOR LEVEL SCORING RULES ---
                1. Persona Validation (+20 pts): Prompt explicitly specifies a role/profession (e.g., tutor, teacher, doctor, lawyer, engineer, scientist, programmer, expert, professor).
                2. Inquiry Structure (+40 pts): Prompt contains interrogative question formatting or ends with a question mark (e.g., starts with what, how, why, can, could, where, who, is, are).
                3. Command Density (+20 pts OR -10 penalty): Must contain AT LEAST 5 action keywords (keywords: explain, summarize, analyze, simplify, debug, format, list, bullet, limit).
                   - If 5+ action keywords are present: +20 points.
                   - If FEWER than 5 action keywords are present: Deduct 10 points (-10 penalty).
                4. Linguistic Expansion (+1 point per word): Add 1 point per word in the user's prompt.
                5. Total Score Rules: Min score = 0, Max capped score = 100.
                
                --- REQUIRED OUTPUT FORMAT ---
                Format your output into three distinct markdown sections:

                ### 📊 Professor Level Prompt Evaluation
                - **Final Score**: [Score]/100
                - **Score Breakdown**:
                  - Persona Validation: [Met / Not Met]
                  - Inquiry Structure: [Met / Not Met]
                  - Command Density: [Met / Failed (-10 Penalty)] (Action keywords found: [count]/5)
                  - Linguistic Expansion: +[word count] points
                
                ### 💡 Constructive Feedback & How to Improve
                Provide clear, actionable advice on how to improve this prompt based on any missed scoring parameters (e.g., adding an expert persona, using 5+ action keywords, or framing a direct question). Show a rewritten 'Master' version of their prompt as an example.

                ---
                ### 🤖 Response to Prompt
                Directly answer the user's original request or question thoroughly and accurately.
                
                User Prompt: "{user_input}"
                """

                with st.chat_message("assistant"):
                    with st.spinner("GramAI Assistant is grading and responding..."):
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=system_evaluation_prompt
                        )
                        st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})

        except Exception as e:
            st.error(f"Gemini API Error: {e}")

    st.write("---")
    col_back, col_clear = st.columns(2)
    with col_back:
        if st.button("↩ Return to Dashboard"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
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
    
    if st.session_state.selected_level == "beginner":
        st.info("💡 **BEGINNER CHALLENGE**: Include a clear persona profile and hit at least **3** action keywords (explain, summarize, analyze, simplify, debug, format, list, bullet, limit).")
    elif st.session_state.selected_level == "advanced":
        st.warning("🔥 **ADVANCED CHALLENGE**: Include an expert profession descriptor and use at least **5** action keywords simultaneously to pass.")
    elif st.session_state.selected_level == "professor":
        st.error("🎓 **PROFESSOR CHALLENGE**: Target strict command dense construction! Must use a professional tone, direct question structure, and **5+** action keywords to prevent point subtraction.")

    st.write(f"**Current Tracker**: Attempt {st.session_state.current_try} / 3")
    user_prompt = st.text_input("Type your test query here:", key="prompt_entry_box")
    
    if st.button("Evaluate Performance", disabled=(st.session_state.current_try > 3)):
        if user_prompt.strip() == "":
            st.error("Please type a prompt first!")
        else:
            score, breakdown = evaluate_prompt_string(user_prompt)
            st.session_state.user_scores.append(score)
            save_score_to_disk(st.session_state.username or "Anonymous", user_prompt, score, st.session_state.selected_level)
            
            results_string = f"Final Score: {score}/100 | " + " | ".join(breakdown)
            st.markdown(f'<div class="white-score-text">{results_string}</div>', unsafe_allow_html=True)
            st.session_state.current_try += 1
                
    if len(st.session_state.user_scores) > 0:
        render_analytics_graph()
        
    if st.button("↩ Back to Menu"):
        st.session_state.current_page = "Home"
        st.rerun()

# --- DYNAMIC SORTED LEADERBOARD LIVE-VIEW ---
st.write("---")
st.subheader("🏆 LIVE TRACK LEADERBOARDS")
selected_board = st.selectbox("View Scoreboard Track:", options=["Beginner Track Logs", "Advanced Track Logs", "Professor Track Logs", "True Master Premium Logs"])
board_mapping = {"Beginner Track Logs": "beginner", "Advanced Track Logs": "advanced", "Professor Track Logs": "professor", "True Master Premium Logs": "true master"}
target_key = board_mapping[selected_board]
target_file_name = SCOREBOARD_FILES[target_key]

if os.path.exists(target_file_name):
    parsed_entries = []
    with open(target_file_name, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            if target_key == "true master":
                user_match = re.search(r"User:\s*([^|]+)", line)
                action_match = re.search(r"Action:\s*(.+)", line)
                u = user_match.group(1).strip() if user_match else "Unknown"
                act = action_match.group(1).strip() if action_match else "N/A"
                parsed_entries.append({"User": u, "Action Logged": act, "_sort_val": 0})
            else:
                user_match = re.search(r"User:\s*([^|]+)", line)
                try_match = re.search(r"Try:\s*(\d+)", line)
                score_match = re.search(r"Score:\s*(\d+)", line)
                prompt_match = re.search(r"Prompt:\s*(.+)", line)
                
                u = user_match.group(1).strip() if user_match else "Unknown"
                t = try_match.group(1).strip() if try_match else "1"
                s = int(score_match.group(1).strip()) if score_match else 0
                p = prompt_match.group(1).strip() if prompt_match else ""
                
                parsed_entries.append({"User": u, "Try": t, "Score": s, "Prompt Provided": p, "_sort_val": s})
    
    if parsed_entries:
        if target_key == "true master":
            st.dataframe(parsed_entries, use_container_width=True)
        else:
            sorted_entries = sorted(parsed_entries, key=lambda x: x["_sort_val"], reverse=True)
            leaderboard_table = []
            for rank_index, item in enumerate(sorted_entries, start=1):
                if rank_index == 1: suffix = "st"
                elif rank_index == 2: suffix = "nd"
                elif rank_index == 3: suffix = "rd"
                else: suffix = "th"
                
                row = {
                    "Rank Placement": f"{rank_index}{suffix}",
                    "User": item["User"],
                    "Score Out of 100": item["Score"],
                    "Attempt Target": item["Try"],
                    "Evaluated Prompt String": item["Prompt Provided"]
                }
                leaderboard_table.append(row)
                
            st.dataframe(leaderboard_table, use_container_width=True)
    else:
        st.info("No active records logged inside this track file yet.")
else:
    st.info("No records recorded for this track yet.")
