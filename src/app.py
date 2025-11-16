# app.py

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv
from utils import extract_video_id, get_transcript
from rag_pipeline import process_transcript, get_answer, get_transcript_summary
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="YouTube AI Chat | Talk to Any Video",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI with 3D effects
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main Background with Animated Gradient */
    .stApp {
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        background-attachment: fixed;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Content Container */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* 3D Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 30px;
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        margin-bottom: 2.5rem;
        animation: fadeInUp 0.8s ease-out;
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(2deg);
        transition: transform 0.3s ease;
    }
    
    .hero-section:hover {
        transform: perspective(1000px) rotateX(0deg) translateY(-5px);
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            transparent,
            rgba(102, 126, 234, 0.1),
            transparent
        );
        transform: rotate(45deg);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        line-height: 1.2;
        text-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 1.4rem;
        color: #4a5568;
        font-weight: 500;
        margin-bottom: 0;
        position: relative;
        z-index: 1;
    }
    
    .hero-emoji {
        font-size: 5rem;
        margin-bottom: 1.5rem;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 10px 20px rgba(102, 126, 234, 0.4));
        position: relative;
        z-index: 1;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        25% { transform: translateY(-10px) rotate(-5deg); }
        75% { transform: translateY(-5px) rotate(5deg); }
    }
    
    /* 3D Input Section */
    .input-section {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 2.5rem;
        border-radius: 25px;
        box-shadow: 
            0 15px 40px rgba(0, 0, 0, 0.2),
            0 5px 15px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
        margin-bottom: 2.5rem;
        transform: perspective(1000px) translateZ(20px);
        transition: all 0.3s ease;
    }
    
    .input-section:hover {
        transform: perspective(1000px) translateZ(30px);
        box-shadow: 
            0 20px 50px rgba(0, 0, 0, 0.25),
            0 10px 20px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
    }
    
    /* 3D Chat Container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 2.5rem;
        border-radius: 25px;
        box-shadow: 
            0 15px 40px rgba(0, 0, 0, 0.2),
            0 5px 15px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
        min-height: 500px;
        margin-bottom: 2rem;
        transform: perspective(1000px) translateZ(20px);
    }
    
    /* Enhanced Chat Messages with 3D effect */
    .stChatMessage {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(247, 250, 252, 0.95) 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 
            0 8px 16px rgba(0, 0, 0, 0.1),
            0 2px 4px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        animation: slideIn 0.4s ease-out;
        border: 1px solid rgba(102, 126, 234, 0.1);
        transform: translateZ(10px);
        transition: all 0.3s ease;
    }
    
    .stChatMessage:hover {
        transform: translateZ(15px) translateY(-2px);
        box-shadow: 
            0 12px 24px rgba(0, 0, 0, 0.15),
            0 4px 8px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
    }
    
    [data-testid="stChatMessageContent"] {
        color: #2d3748;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    
    /* 3D Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.98) 0%, rgba(118, 75, 162, 0.98) 100%);
        backdrop-filter: blur(20px);
        box-shadow: 5px 0 30px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: white;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* 3D Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.9rem 2.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        box-shadow: 
            0 6px 20px rgba(102, 126, 234, 0.4),
            0 2px 5px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        transform: translateZ(10px);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateZ(15px) translateY(-3px);
        box-shadow: 
            0 10px 30px rgba(102, 126, 234, 0.6),
            0 4px 10px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    .stButton > button:active {
        transform: translateZ(5px) translateY(-1px);
    }
    
    /* Enhanced Text Input with 3D effect */
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        padding: 1rem 1.5rem;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        background: white;
        box-shadow: 
            inset 0 2px 4px rgba(0, 0, 0, 0.06),
            0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 
            0 0 0 4px rgba(102, 126, 234, 0.1),
            inset 0 2px 4px rgba(0, 0, 0, 0.06),
            0 4px 12px rgba(102, 126, 234, 0.2);
        transform: translateY(-1px);
    }
    
    /* 3D Feature Cards */
    .feature-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 
            0 10px 25px rgba(0, 0, 0, 0.1),
            0 3px 8px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: 1px solid rgba(102, 126, 234, 0.1);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) translateZ(0);
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .feature-card:hover::before {
        opacity: 1;
    }
    
    .feature-card:hover {
        transform: perspective(1000px) translateZ(20px) translateY(-8px) rotateX(5deg);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.15),
            0 8px 16px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.3));
        animation: iconBounce 2s ease-in-out infinite;
    }
    
    @keyframes iconBounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.8rem;
    }
    
    .feature-desc {
        font-size: 1rem;
        color: #718096;
        line-height: 1.6;
    }
    
    /* 3D Stats Badge */
    .stats-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.7rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        margin: 0.5rem;
        box-shadow: 
            0 6px 15px rgba(102, 126, 234, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        transform: translateZ(5px);
    }
    
    .stats-badge:hover {
        transform: translateZ(10px) translateY(-2px);
        box-shadow: 
            0 8px 20px rgba(102, 126, 234, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    /* Enhanced Messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 15px;
        padding: 1.2rem;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(102, 126, 234, 0.2);
        transform: translateX(5px);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: perspective(1000px) translateY(40px) rotateX(-10deg);
        }
        to {
            opacity: 1;
            transform: perspective(1000px) translateY(0) rotateX(0deg);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Decorative Elements */
    .decorative-shape {
        position: fixed;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.3;
        pointer-events: none;
        z-index: -1;
    }
    
    .shape-1 {
        width: 300px;
        height: 300px;
        background: #667eea;
        top: 10%;
        left: 5%;
        animation: float 8s ease-in-out infinite;
    }
    
    .shape-2 {
        width: 250px;
        height: 250px;
        background: #764ba2;
        bottom: 15%;
        right: 10%;
        animation: float 10s ease-in-out infinite reverse;
    }
    
    .shape-3 {
        width: 200px;
        height: 200px;
        background: #f093fb;
        top: 50%;
        right: 5%;
        animation: float 12s ease-in-out infinite;
    }
    </style>
    
    <!-- Decorative floating shapes -->
    <div class="decorative-shape shape-1"></div>
    <div class="decorative-shape shape-2"></div>
    <div class="decorative-shape shape-3"></div>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        "vector_store": None,
        "messages": [],
        "video_id": None,
        "video_url": "",
        "transcript": None,
        "detected_language": None,
        "llm": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _get_language_display(lang_code: str) -> str:
    """Get display name for language."""
    language_map = {
        'hi': '🇮🇳 Hindi (हिंदी)',
        'en': '🇬🇧 English',
        'en-US': '🇺🇸 English (US)',
        'en-GB': '🇬🇧 English (UK)',
        'es': '🇪🇸 Spanish',
        'fr': '🇫🇷 French',
        'de': '🇩🇪 German',
        'pt': '🇵🇹 Portuguese',
        'ar': '🇸🇦 Arabic',
        'bn': '🇧🇩 Bengali',
        'te': '🇮🇳 Telugu',
        'mr': '🇮🇳 Marathi',
        'ta': '🇮🇳 Tamil',
        'ur': '🇵🇰 Urdu',
        'gu': '🇮🇳 Gujarati',
        'kn': '🇮🇳 Kannada',
        'ml': '🇮🇳 Malayalam',
        'pa': '🇮🇳 Punjabi',
        'auto': '🌐 Auto-detected',
        'unknown': '❓ Unknown'
    }
    return language_map.get(lang_code, f'🌐 {lang_code.upper()}')

initialize_session_state()

# Initialize LLM if not exists
if st.session_state.llm is None:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not OPENAI_API_KEY:
        st.error("⚠️ OPENAI_API_KEY not found in environment variables!")
        st.info("Please create a .env file with: OPENAI_API_KEY=your_key_here")
        st.stop()
    
    try:
        st.session_state.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=OPENAI_API_KEY
        )
    except Exception as e:
        st.error(f"Failed to initialize OpenAI: {e}")
        st.stop()

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='color: white; text-align: center; margin-bottom: 2rem;'>⚙️ Dashboard</h2>", unsafe_allow_html=True)
    
    # Display current video info
    if st.session_state.video_id:
        detected_lang = st.session_state.get('detected_language', 'unknown')
        lang_display = _get_language_display(detected_lang)
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);'>
                <p style='color: white; margin: 0; font-weight: 700; font-size: 1.1rem;'>📹 Active Video</p>
                <p style='color: rgba(255,255,255,0.9); margin: 0.8rem 0 0 0; font-size: 0.95rem; font-weight: 500;'>{st.session_state.video_id}</p>
                <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{lang_display}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Show transcript preview
        if st.session_state.transcript:
            with st.expander("📄 Transcript Preview", expanded=False):
                st.text_area("", st.session_state.transcript[:500] + "...", height=150, disabled=True)
        
        # Summary button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate Summary", use_container_width=True):
            with st.spinner("Creating summary..."):
                summary = get_transcript_summary(
                    st.session_state.vector_store,
                    st.session_state.llm
                )
                st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 15px; margin-top: 1rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px);'>
                        <p style='color: white; font-size: 0.95rem; line-height: 1.7;'>{summary}</p>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Reset button
    if st.button("🔄 New Video", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key != 'llm':
                del st.session_state[key]
        st.rerun()
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Features
    st.markdown("<h3 style='color: white; margin-bottom: 1rem;'>✨ Features</h3>", unsafe_allow_html=True)
    st.markdown("""
        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 2;'>
        🎯 AI-powered answers<br>
        🚀 Lightning fast search<br>
        📝 Smart summaries<br>
        💬 Natural conversations<br>
        🌐 Multi-language support<br>
        🔒 Secure & private
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Instructions
    with st.expander("📖 How to Use"):
        st.markdown("""
        **Getting Started:**
        1. Paste any YouTube URL
        2. Click "Load Video"
        3. Wait for processing
        4. Ask questions in any language!
        
        **Supported Languages:**
        - 🇮🇳 Hindi (हिंदी)
        - 🇬🇧 English
        - 🇪🇸 Spanish
        - 🇫🇷 French
        - And 15+ more languages!
        
        **Supported URLs:**
        - youtube.com/watch?v=...
        - youtu.be/...
        - youtube.com/shorts/...
        """)
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; color: rgba(255,255,255,0.7); font-size: 0.85rem;'>
            Made with ❤️ using<br>
            <strong>OpenAI & LangChain</strong>
        </div>
    """, unsafe_allow_html=True)

# Main content area
# Hero Section with 3D effect
st.markdown("""
    <div class='hero-section'>
        <div class='hero-emoji'>🎬</div>
        <h1 class='hero-title'>YouTube AI Chat</h1>
        <p class='hero-subtitle'>Transform any YouTube video into an intelligent conversation</p>
    </div>
""", unsafe_allow_html=True)

# Input Section
st.markdown("<div class='input-section'>", unsafe_allow_html=True)

# Tabs for URL or Manual Transcript
tab1, tab2 = st.tabs(["📺 From YouTube URL", "📝 Paste Transcript Manually"])

with tab1:
    col1, col2 = st.columns([5, 1])
    
    with col1:
        video_url = st.text_input(
            "🔗 Enter YouTube Video URL",
            value=st.session_state.video_url,
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="url_input"
        )
    
    with col2:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        load_button = st.button("🚀 Load", type="primary", use_container_width=True, key="load_url")

with tab2:
    st.markdown("**If YouTube is rate-limiting, you can manually paste the transcript:**")
    st.markdown("1. Go to the YouTube video")
    st.markdown("2. Click '...' → 'Show transcript'")
    st.markdown("3. Copy all the text and paste below")
    
    manual_transcript = st.text_area(
        "Paste transcript here:",
        height=200,
        placeholder="Paste the video transcript here...",
        key="manual_transcript"
    )
    
    manual_load_button = st.button("📥 Load Manual Transcript", type="primary", use_container_width=True, key="load_manual")

st.markdown("</div>", unsafe_allow_html=True)

# Process video when URL is provided
if video_url and (load_button or video_url != st.session_state.video_url):
    video_id = extract_video_id(video_url)
    
    if not video_id:
        st.error("❌ Invalid YouTube URL. Please check and try again.")
    elif video_id != st.session_state.video_id:
        # New video - process it
        st.session_state.video_url = video_url
        
        with st.status("🎬 Processing your video...", expanded=True) as status:
            st.write("🔍 Extracting video ID...")
            st.write(f"📹 Video ID: `{video_id}`")
            
            st.write("📥 Fetching transcript...")
            result = get_transcript(video_id)
            
            if result[0] is None:
                status.update(label="❌ Failed to load transcript", state="error")
                st.error("Could not fetch transcript. The video might not have captions enabled.")
                st.stop()
            
            transcript, detected_lang = result
            lang_name = _get_language_display(detected_lang)
            
            st.write(f"✅ Transcript loaded in {lang_name} ({len(transcript):,} characters)")
            
            st.write("🔄 Processing and embedding transcript...")
            try:
                vector_store = process_transcript(transcript)
                
                # Update session state
                st.session_state.vector_store = vector_store
                st.session_state.video_id = video_id
                st.session_state.transcript = transcript
                st.session_state.detected_language = detected_lang
                st.session_state.messages = []  # Clear chat history for new video
                
                status.update(label="✅ Video ready for chat!", state="complete")
                st.balloons()
                st.success("🎉 Success! Start chatting with your video below.")
                
            except Exception as e:
                status.update(label="❌ Processing failed", state="error")
                st.error(f"Error processing transcript: {e}")
                st.stop()
    else:
        st.info("ℹ️ This video is already loaded. Ask questions below!")

# Chat interface
if st.session_state.vector_store:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("""
        <h2 style='text-align: center; color: #2d3748; margin-bottom: 2rem; 
                   font-weight: 700; font-size: 2rem;'>
            💬 Chat with Your Video
        </h2>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if user_question := st.chat_input("💭 Ask anything about the video..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
        
        st.session_state.messages.append({
            "role": "user",
            "content": user_question
        })
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                answer = get_answer(
                    user_question,
                    st.session_state.vector_store,
                    st.session_state.llm
                )
            st.markdown(answer)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # Welcome message when no video is loaded
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Feature Grid with perfect alignment
    st.markdown("<div style='margin: 2rem 0;'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""
            <div class='feature-card'>
                <div style='text-align: center;'>
                    <div class='feature-icon'>🎯</div>
                    <div class='feature-title'>Instant Answers</div>
                    <div class='feature-desc'>Get precise answers from any YouTube video in seconds with AI-powered search</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class='feature-card'>
                <div style='text-align: center;'>
                    <div class='feature-icon'>🧠</div>
                    <div class='feature-title'>AI-Powered</div>
                    <div class='feature-desc'>Powered by GPT-4 with multilingual support for 20+ languages worldwide</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class='feature-card'>
                <div style='text-align: center;'>
                    <div class='feature-icon'>⚡</div>
                    <div class='feature-title'>Lightning Fast</div>
                    <div class='feature-desc'>Advanced semantic search finds relevant content instantly with precision</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Stats section
    st.markdown("<div style='text-align: center; margin: 3rem 0 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
        <h3 style='color: #2d3748; font-weight: 700; margin-bottom: 1.5rem; font-size: 1.8rem;'>
            🌟 Trusted by Users Worldwide
        </h3>
    """, unsafe_allow_html=True)
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>20+</div>
                <div style='color: #718096; font-weight: 600; margin-top: 0.5rem;'>Languages</div>
            </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>AI</div>
                <div style='color: #718096; font-weight: 600; margin-top: 0.5rem;'>Powered</div>
            </div>
        """, unsafe_allow_html=True)
    
    with stat_col3:
        st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>⚡</div>
                <div style='color: #718096; font-weight: 600; margin-top: 0.5rem;'>Fast Search</div>
            </div>
        """, unsafe_allow_html=True)
    
    with stat_col4:
        st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🔒</div>
                <div style='color: #718096; font-weight: 600; margin-top: 0.5rem;'>Secure</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Example queries with better alignment
    st.markdown("<div style='margin: 3rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
        <h3 style='text-align: center; color: #2d3748; margin-bottom: 2rem; font-weight: 700; font-size: 1.8rem;'>
            💡 Example Questions
        </h3>
    """, unsafe_allow_html=True)
    
    example_col1, example_col2 = st.columns(2, gap="large")
    
    with example_col1:
        st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%); 
                        padding: 1.5rem; border-radius: 15px; margin: 0.8rem 0; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #667eea;
                        transition: all 0.3s ease;' 
                 onmouseover='this.style.transform="translateX(5px)"; this.style.boxShadow="0 6px 16px rgba(0,0,0,0.12)";'
                 onmouseout='this.style.transform="translateX(0)"; this.style.boxShadow="0 4px 12px rgba(0,0,0,0.08)";'>
                <p style='margin: 0; color: #2d3748; font-weight: 600; font-size: 1.05rem;'>❓ "What is the main topic?"</p>
                <p style='margin: 0.5rem 0 0 0; color: #718096; font-size: 0.9rem;'>मुख्य विषय क्या है?</p>
            </div>
            <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%); 
                        padding: 1.5rem; border-radius: 15px; margin: 0.8rem 0; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #764ba2;
                        transition: all 0.3s ease;'
                 onmouseover='this.style.transform="translateX(5px)"; this.style.boxShadow="0 6px 16px rgba(0,0,0,0.12)";'
                 onmouseout='this.style.transform="translateX(0)"; this.style.boxShadow="0 4px 12px rgba(0,0,0,0.08)";'>
                <p style='margin: 0; color: #2d3748; font-weight: 600; font-size: 1.05rem;'>📊 "What examples were given?"</p>
                <p style='margin: 0.5rem 0 0 0; color: #718096; font-size: 0.9rem;'>कौन से उदाहरण दिए गए?</p>
            </div>
        """, unsafe_allow_html=True)
    
    with example_col2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%); 
                        padding: 1.5rem; border-radius: 15px; margin: 0.8rem 0; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #f093fb;
                        transition: all 0.3s ease;'
                 onmouseover='this.style.transform="translateX(5px)"; this.style.boxShadow="0 6px 16px rgba(0,0,0,0.12)";'
                 onmouseout='this.style.transform="translateX(0)"; this.style.boxShadow="0 4px 12px rgba(0,0,0,0.08)";'>
                <p style='margin: 0; color: #2d3748; font-weight: 600; font-size: 1.05rem;'>📝 "Summarize the key points"</p>
                <p style='margin: 0.5rem 0 0 0; color: #718096; font-size: 0.9rem;'>मुख्य बिंदुओं का सारांश दें</p>
            </div>
            <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%); 
                        padding: 1.5rem; border-radius: 15px; margin: 0.8rem 0; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid #4facfe;
                        transition: all 0.3s ease;'
                 onmouseover='this.style.transform="translateX(5px)"; this.style.boxShadow="0 6px 16px rgba(0,0,0,0.12)";'
                 onmouseout='this.style.transform="translateX(0)"; this.style.boxShadow="0 4px 12px rgba(0,0,0,0.08)";'>
                <p style='margin: 0; color: #2d3748; font-weight: 600; font-size: 1.05rem;'>🎓 "What did they say about X?"</p>
                <p style='margin: 0.5rem 0 0 0; color: #718096; font-size: 0.9rem;'>X के बारे में क्या कहा?</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Footer with better alignment
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; padding: 2.5rem; 
                background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(247, 250, 252, 0.95) 100%); 
                border-radius: 20px; margin-top: 2.5rem;
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);'>
        <p style='color: #4a5568; margin: 0; font-size: 1rem; font-weight: 500;'>
            Built with ❤️ using <strong style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Streamlit</strong>, 
            <strong style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>LangChain</strong> & 
            <strong style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>OpenAI</strong>
        </p>
        <p style='color: #718096; margin: 1rem 0 0 0; font-size: 0.9rem;'>
            <a href='https://github.com' style='color: #667eea; text-decoration: none; font-weight: 600; 
               transition: all 0.3s ease;' 
               onmouseover='this.style.color="#764ba2";' 
               onmouseout='this.style.color="#667eea";'>
                ⭐ Star on GitHub
            </a> | 
            <a href='#' style='color: #667eea; text-decoration: none; font-weight: 600;
               transition: all 0.3s ease;'
               onmouseover='this.style.color="#764ba2";' 
               onmouseout='this.style.color="#667eea";'>
                📧 Contact Us
            </a>
        </p>
    </div>
""", unsafe_allow_html=True)