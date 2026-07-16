import streamlit as st
import matplotlib.pyplot as plt
import os

# --- PERSISTENT DATA CONTROL LAYER ---
DATA_FILE = "science_fair_metrics.txt"

# We use Streamlit's session state to maintain global variables across browser refreshes
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

def save_score_to_disk(username, prompt, score):
    """
    SCIENCE FAIR METHOD: Appends empirical execution tracking records to a structured log file.
    """
    try:
        with open(DATA_FILE, "a", encoding="utf-8") as file:
            file.write(f"User: {username} | Try: {st.session_state.current_try} | Score: {score} | Prompt: {prompt}\n")
    except Exception as e:
        st.error(f"Data Write Failure: {e}")

# --- PROMPT EVALUATION ENGINE ---
def evaluate_prompt_string(prompt):
    score = 0
    metrics_passed = []
    lowered = prompt.lower()
    words_list = prompt.split()
    word_count = len(words_list)

    if word_count == 0:
        return 0, ["❌ Empty query string flagged."]

    # 1. Profession Check
    professions = ["tutor", "teacher", "doctor", "lawyer", "engineer", "scientist",
                   "programmer", "coder", "developer", "expert", "professor", "assistant"]
    if any(prof in lowered for prof in professions):
        score += 20
        metrics_passed.append("Role Persona Met (+20)")
    else:
        metrics_passed.append("Missing Persona constraints.")

    # 2. Direct Question Check
    question_starters = ["what", "how", "why", "can", "could", "where", "who", "is", "are"]
    has_question_word = any(lowered.startswith(start) for start in question_starters)
    if prompt.endswith("?") or has_question_word:
        score += 40
        metrics_passed.append("Direct Question parameters identified (+40)")
    else:
        metrics_passed.append("Missing explicit interrogative query structure.")

    # 3. Dynamic Keywords Check
    action_keywords = ["explain", "summarize", "analyze", "simplify", "debug",
                       "format", "list", "bullet", "limit", "words", "paragraphs"]
    found_keywords = [kw for kw in action_keywords if kw in lowered]

    required_count = 5 if st.session_state.selected_level in ["advanced", "professor"] else 3

    if len(found_keywords) >= required_count:
        score += 20
        metrics_passed.append(f"Keyword Limit Met ({len(found_keywords)}/{required_count}) (+20)")
    else:
        metrics_passed.append(f"Keyword Challenge Failed ({len(found_keywords)}/{required_count})")

    # 4. Word Count Check
    score += word_count
    metrics_passed.append(f"Linguistic Scale Expansion: +{word_count} Points")

    # 5. Professor Level Structural Checks
    if st.session_state.selected_level == "professor":
        professor_passed_all = True

        has_reason = any(term in lowered for term in ["because", "to help", "in order to", "since", "why", "for"])
        if not has_reason:
            professor_passed_all = False
            metrics_passed.append("❌ Missing justification clause ('because...', 'to help...')")

        has_length_spec = any(term in lowered for term in ["long", "short", "length", "words", "sentences", "paragraphs"])
        if not has_length_spec:
            professor_passed_all = False
            metrics_passed.append("❌ Missing response length constraint specifications")

        has_layout_style = any(term in lowered for term in ["paragraph", "list", "bullet", "bullets", "points"])
        if not has_layout_style:
            professor_passed_all = False
            metrics_passed.append("❌ Missing layout style choice ('paragraph', 'list', or 'bullet points')")

        if word_count < 30:
            professor_passed_all = False
            metrics_passed.append(f"❌ Under minimum length constraint ({word_count}/30 words)")

        if professor_passed_all:
            score += 50
            metrics_passed.append("⭐ PERFECT PROFESSOR PROMPT CORE CRITERIA MET! (+50)")

    return score, metrics_passed

# --- GRAPH RENDERER ---
def render_analytics_graph():
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor('#111E25')
    ax.set_facecolor('#1c2d37')

    attempts = [1, 2, 3]
    padded_scores = st.session_state.user_scores + [0] * (3 - len(st.session_state.user_scores))

    ax.plot(attempts, padded_scores, marker='o', color='#81C784', linewidth=2, markersize=6)
    ax.set_title("Prompt Iteration Learning Chart", color='white', fontsize=10, fontweight='bold')
    ax.set_ylabel("Matrix Score Output", color='white', fontsize=8)
    ax.set_xticks(attempts)
    ax.set_xticklabels(["Try 1", "Try 2", "Try 3"], color='white', fontsize=8)
    ax.tick_params(colors='white', labelsize=8)
    ax.set_ylim(0, 180)
    ax.grid(True, color='#2c3d47', linestyle='--')
    
    st.pyplot(fig)

# --- EDUCATIONAL TOPIC DATA ---
TOPICS = {
    "beginner": {
        "keywords": {
            "title": "How to use keywords",
            "desc": "Keywords act as signposts for AI systems. By incorporating precise, descriptive terms (like 'summarize', 'bullet points', or specific professional roles), you minimize ambiguity.",
            "url": "https://www.searchenginejournal.com/keyword-research/"
        },
        "why_ai": {
            "title": "Why should I use AI",
            "desc": "AI handles repetitive tasks, debugs code, structures complex data, and provides immediate problem-solving analytics as a productivity multiplier.",
            "url": "https://www.ibm.com/topics/artificial-intelligence"
        },
        "how_ai_works": {
            "title": "How does AI work",
            "desc": "Modern AI relies on Neural Networks and Machine Learning. It processes vast datasets to identify mathematical patterns, predicting words or actions.",
            "url": "https://www.bbc.com/news/technology-65824143"
        }
    },
    "advanced": {
        "how_use_ai": {
            "title": "How should I use AI",
            "desc": "Advanced users focus on integration parameters: engineering targeted system prompts, chain-of-thought instructions, and providing context constraint criteria.",
            "url": "https://www.zdnet.com/article/how-to-use-chatgpt/"
        },
        "pros_cons_ai": {
            "title": "Pros and cons of AI",
            "desc": "Pros: Extreme cognitive acceleration and pattern parsing. Cons: Hallucination risks, structural dataset bias, and massive computational overhead requirements.",
            "url": "https://www.forbes.com/sites/bernardmarr/2023/06/02/the-pros-and-cons-of-artificial-intelligence-everyone-should-know/"
        },
        "what_llms": {
            "title": "What are LLMs",
            "desc": "LLMs are foundational deep learning algorithms trained on billions of parameters using transformer models to analyze sequential text input tokens.",
            "url": "https://www.cloudflare.com/learning/ai/what-is-large-language-model/"
        }
    },
    "professor": {
        "ai_literacy_stats": {
            "title": "How many people are AI literate",
            "desc": "Global assessments indicate that basic digital usage is widespread, but true AI literacy—data pipelines and algorithmic bias evaluation—remains below 25%.",
            "url": "https://www.unesco.org/en/articles/ai-competency-frameworks-school-students-and-teachers"
        },
        "class_disparities": {
            "title": "Socio-economic class disparities",
            "desc": "The 'AI Divide' shadows traditional financial wealth. High-income areas benefit from early platform subscription access and integrated school curricula.",
            "url": "https://www.worldbank.org/en/topic/digital-development/overview"
        },
        "tech_behind_countries": {
            "title": "Countries furthest behind in tech",
            "desc": "Developing and post-conflict nations face structural grid instability and lack of fiber infrastructure, limiting participation in cloud scaling models.",
            "url": "https://www.un.org/en/un75/impact-digital-technologies"
        }
    }
}

# --- WEB APP NAVIGATION & LAYOUT ---
st.set_page_config(page_title="Professor AI", page_icon="🤖", layout="centered")

# Custom Styling (Mint/Teal layout)
st.markdown("""
    <style>
    .stApp { background-color: #7FFFD4; color: #111E25; }
    h1, h2, h3 { color: #111E25 !important; }
    div.stButton > button { background-color: #111E25; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Navigation Router
if st.session_state.current_page == "Home":
    st.title("🤖 Professor AI")
    st.subheader("Welcome to Professor AI")
    if st.button("Launch Application ➔"):
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
            st.success(f"Username '{st.session_state.username}' saved successfully!")
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
    
    col1, col2, col3 = st.columns(3)
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

elif st.session_state.current_page == "Syllabus":
    st.title("Dynamic Learning Portal")
    st.subheader(f"Track: {st.session_state.selected_level.capitalize()}")
    
    # Render Lesson Selections
    level_data = TOPICS[st.session_state.selected_level]
    
    cols = st.columns(3)
    for index, (key, data) in enumerate(level_data.items()):
        with cols[index]:
            if st.button(data["title"], use_container_width=True):
                st.session_state.selected_topic = data

    if st.session_state.selected_topic:
        st.info(st.session_state.selected_topic["desc"])
        st.markdown(f"[🔗 Lesson Resources]({st.session_state.selected_topic['url']})")

    st.write("---")
    if st.button("Proceed to Analytics Test ➔"):
        # Initialize Test parameters cleanly
        st.session_state.current_try = 1
        st.session_state.user_scores = []
        st.session_state.current_page = "Test Lab"
        st.rerun()

elif st.session_state.current_page == "Test Lab":
    st.title("🧪 Prompt Assessment Engine Lab")
    
    # Challenge instructions box
    if st.session_state.selected_level == "professor":
        st.warning("🎓 PROFESSOR CHALLENGE: 5 keywords, state your AI use-case reason, length preference, format style, & min 30 words!")
    elif st.session_state.selected_level == "advanced":
        st.warning("🔥 ADVANCED CHALLENGE: You must hit at least 5 distinct action keywords!")
    else:
        st.info("💡 BEGINNER CHALLENGE: Try including at least 3 action keywords.")

    st.write(f"**Current Attempt Tracker**: Attempt {st.session_state.current_try} / 3")
    
    user_prompt = st.text_input("Type your test query here:", key="prompt_entry_box")
    
    if st.button("Evaluate Query Performance", disabled=(st.session_state.current_try > 3)):
        if user_prompt.strip() == "":
            st.error("Please type a prompt first!")
        else:
            score, breakdown = evaluate_prompt_string(user_prompt)
            st.session_state.user_scores.append(score)
            save_score_to_disk(st.session_state.username or "Anonymous", user_prompt, score)
            
            st.success(f"Score: {score} Points | " + " | ".join(breakdown[:3]))
            
            if st.session_state.current_try >= 3:
                st.session_state.current_try = 4 # Complete flag
            else:
                st.session_state.current_try += 1
                
    # Graph Area
    if len(st.session_state.user_scores) > 0:
        render_analytics_graph()

    # Reset or Complete Status Pop-ups
    if st.session_state.current_try > 3:
        st.error("Testing Cycle Terminated (3/3 Tries Exhausted)")
        improvement = st.session_state.user_scores[-1] - st.session_state.user_scores[0]
        st.metric(label="Optimization Trajectory Variance", value=f"+{improvement} Points")
        
    if st.button("↩ Back to Menu"):
        st.session_state.current_page = "Home"
        st.rerun()
