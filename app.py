# app.py

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from utils import (
    configure_openai, load_data, classify_prompt_and_extract_entities,
    search_data, get_ai_response, get_no_data_suggestion
)

from visualizations import (
    display_summary_metrics, plot_sentiment_distribution, plot_engagement_by_category,
    plot_time_series, plot_followers_vs_engagement, display_top_viral_posts,
    display_data_context, display_top_performers, plot_geospatial_analysis,
    plot_performance_quadrant, display_top_followers_posts,
    display_top_engagement_posts, plot_source_distribution # <-- ADD THIS IMPORT
)

from components import (
    apply_custom_css, display_raw_data_bubbles, display_history, display_header_logo
)
import history_service  # ADDED: Import the new service for handling chat history files

# --- PAGE CONFIG & SETUP ---
st.set_page_config(page_title="AI Social Media Dashboard", page_icon="logo_kurasi.png" ,layout="wide", initial_sidebar_state="expanded")

# Automatically scroll to top on rerun
components.html("<script>window.scrollTo(0, 0);</script>", height=0)

apply_custom_css()
configure_openai()
df = load_data()

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "matched_data" not in st.session_state:
    st.session_state.matched_data = pd.DataFrame()
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False
if "last_search" not in st.session_state:
    st.session_state.last_search = {"strict_groups": [], "fallback_keywords": []}
# REMOVED: The state for decoupled AI response is no longer needed

# --- SIDEBAR ---
with st.sidebar:
    display_header_logo()
    
    st.markdown("""
    <h3 style="display:flex; align-items:center; gap:6px; margin-bottom:10px;">
    <i class="bi bi-clock-history"></i> History Percakapan
    </h3>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .new-chat-btn {
    background-color: #c7a4ff;  /* ungu muda */
    color: white;               /* teks putih */
    border: none;
    border-radius: 10px;        /* sudut membulat */
    padding: 10px 16px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    width: 100%;                /* biar penuh kayak st.button */
    text-align: left;           /* biar ikon + teks rapih */
    }

    .new-chat-btn:hover {
    background-color: #b388ff;  /* ungu muda lebih gelap saat hover */
    }

    .new-chat-btn::before {
    font-family: bootstrap-icons !important;
    content: "\\f4d2"; /* bi-plus-circle */
    margin-right: 8px;
    font-size: 16px;
    vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <button class="new-chat-btn">
    Percakapan Baru
    </button>
    """, unsafe_allow_html=True)

    display_history()

    # Tombol logout
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["messages"] = []
        st.session_state["matched_data"] = pd.DataFrame()
        st.session_state["search_performed"] = False
        st.session_state["last_search"] = {"strict_groups": [], "fallback_keywords": []}
        st.rerun()


# --- MAIN LAYOUT (3 COLUMNS) ---
col1, col2, col3 = st.columns([2, 2.5, 2])

# --- COLUMN 1: CHAT INTERFACE ---
with col1:
     
    st.markdown(
        "<h3 style='display:flex; align-items:center; gap:8px; color:#2F5D9F;'>"
        "<i class='bi bi-robot'></i> AI Assistant</h3>",
        unsafe_allow_html=True
    )

    chat_container = st.container(height=550, border=True)

    # Display chat history with custom bubble styling
    for message in st.session_state.messages:
        content_for_html = message["content"].replace("\n", "<br>")
        
        if message["role"] == "user":
            chat_container.markdown(
                f'<div class="chat-bubble chat-human">{content_for_html}</div>',
                unsafe_allow_html=True
            )
        else:
            chat_container.markdown(
                f'<div class="chat-bubble chat-ai">{content_for_html}</div>',
                unsafe_allow_html=True
            )


# --- COLUMN 2: VISUALIZATIONS ---
with col2:
    st.markdown(
        "<h3 style='display:flex; align-items:center; gap:8px; color:#2F5D9F;'>"
        "<i class='bi bi-bar-chart-line'></i> Visualisasi Data</h3>",
        unsafe_allow_html=True
    )
    with st.container(height=550, border=True):
        if not st.session_state.search_performed:
            st.info("Masukan pertanyaan Anda di kolom chat untuk memulai.")
        elif st.session_state.matched_data.empty:
            st.warning("Tidak ada data yang ditemukan untuk kriteria pencarian Anda.")
        else:
            data_for_viz = st.session_state.matched_data.copy()

            display_data_context(data_for_viz, st.session_state.last_search)

            tabs = st.tabs([
                            "Summary", "Sentiment" ,"Engagement", "Trends",
                            "Performance","Top Performers", "Geospatial"
                            ])
 
            with tabs[0]: # Summary
                display_summary_metrics(data_for_viz)
                st.markdown("---") 

                # NEW ORDER
                display_top_engagement_posts(data_for_viz) # <-- ADD THIS
                st.markdown("---") 
                display_top_viral_posts(data_for_viz)
                st.markdown("---") 
                display_top_followers_posts(data_for_viz)
            
            
            with tabs[1]: # Sentiment
                plot_sentiment_distribution(data_for_viz)
            with tabs[2]: # Engagement
                plot_engagement_by_category(data_for_viz, category='TOPIK')
                plot_engagement_by_category(data_for_viz, category='GRUP')
            with tabs[3]: # Trends
                plot_time_series(data_for_viz)
                plot_source_distribution(data_for_viz) 
            with tabs[4]: # Performance
                plot_followers_vs_engagement(data_for_viz)
                st.markdown("---") # Add a separator
                plot_performance_quadrant(data_for_viz)
            with tabs[5]: # Top Performers
                display_top_performers(data_for_viz)
            with tabs[6]: # Geospatial
                plot_geospatial_analysis(data_for_viz)

# --- COLUMN 3: RAW DATA ---
with col3:
    st.markdown(
        "<h3 style='display:flex; align-items:center; gap:8px; color:#2F5D9F;'>"
        "<i class='bi bi-table'></i> Data Konten</h3>",
        unsafe_allow_html=True
    )
    with st.container(height=550, border=True):
        display_raw_data_bubbles(st.session_state.matched_data)

# --- CHAT INPUT & SEQUENTIAL PROCESSING ---
if prompt := st.chat_input("Ask about the data..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # All processing happens sequentially here
    response_stream = None
    with st.spinner("Analyzing prompt and generating response..."):
        # STEP 1: Analyze prompt and search for data
        user_messages = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        previous_prompt = user_messages[-2] if len(user_messages) > 1 else ""
        analysis = classify_prompt_and_extract_entities(prompt, previous_prompt)

        prompt_type = analysis.get("type")
        dates = analysis.get("dates", [])

        if st.session_state.matched_data.empty and len(st.session_state.messages) > 2:
            prompt_type = "New Topic"
            analysis = classify_prompt_and_extract_entities(prompt, "")

        if prompt_type == "New Topic" and not dates:
            st.session_state.search_performed = False
            st.session_state.matched_data = pd.DataFrame()
            strict_groups = analysis.get("strict_groups", [])
            fallback_keywords = analysis.get("fallback_keywords", [])
            st.session_state.last_search = {"strict_groups": strict_groups, "fallback_keywords": fallback_keywords}

            def missing_date_response():
                response_text = "Tentu, saya bisa carikan datanya. Mohon informasikan tanggal atau rentang tanggal spesifik yang Anda inginkan."
                for word in response_text.split():
                    import time
                    yield word + " "
                    time.sleep(0.05)
            response_stream = missing_date_response()
        else:
            if prompt_type == "New Topic":
                strict_groups = analysis.get("strict_groups", [])
                fallback_keywords = analysis.get("fallback_keywords", [])
                st.session_state.last_search = {"strict_groups": strict_groups, "fallback_keywords": fallback_keywords}
                st.session_state.matched_data = search_data(df, strict_groups, fallback_keywords, dates)
            elif prompt_type == "Follow-Up":
                last_search_params = st.session_state.last_search
                if dates:
                    st.session_state.matched_data = search_data(df, last_search_params["strict_groups"], last_search_params["fallback_keywords"], dates)

            st.session_state.search_performed = True
        
            # STEP 2: Get AI response stream (now happens after data search)
            response_stream = get_ai_response(prompt, st.session_state.matched_data, st.session_state.last_search)

    # STEP 3: Stream response to UI
    if response_stream:
        # We add the user message to the display *just before* the AI starts responding
        chat_container.markdown(
            f'<div class="chat-bubble chat-human">{prompt.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )
        
        placeholder = chat_container.empty()
        full_response = ""
        for chunk in response_stream:
            full_response += chunk
            response_for_html = full_response.replace("\n", "<br>")
            placeholder.markdown(
                f'<div class="chat-bubble chat-ai">{response_for_html}</div>',
                unsafe_allow_html=True
            )

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # STEP 4: Save history and rerun the app to finalize the display
    if prompt_type == "New Topic" and not st.session_state.matched_data.empty:
        current_session_state = {
            "messages": st.session_state.get("messages", []).copy(),
            "matched_data": st.session_state.get("matched_data", pd.DataFrame()).copy(),
            "last_search": st.session_state.get("last_search", {}).copy()
        }
        history_service.save_chat_session(current_session_state)

    st.rerun()

    