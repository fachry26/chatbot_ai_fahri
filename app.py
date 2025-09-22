# app.py

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from utils import (
    configure_openai, load_data, classify_prompt_and_extract_entities,
    search_data, get_ai_response, get_no_data_suggestion
)
# In app.py
from visualizations import (
    display_summary_metrics, plot_sentiment_distribution, plot_engagement_by_category,
    plot_time_series, plot_followers_vs_engagement, display_top_viral_posts,
    display_data_context, display_top_performers, plot_geospatial_analysis,
    plot_performance_quadrant # <-- ADD THIS IMPORT
)
from components import (
    apply_custom_css, display_raw_data_bubbles, display_history, display_header_logo
)

# --- PAGE CONFIG & SETUP ---
st.set_page_config(page_title="AI Social Media Dashboard", layout="wide", initial_sidebar_state="expanded")

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
if "history" not in st.session_state:
    st.session_state.history = []

# --- SIDEBAR ---
with st.sidebar:
    display_header_logo()
    st.subheader("📖 History")
    display_history(st.session_state.history)

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.matched_data = pd.DataFrame()
        st.session_state.search_performed = False
        st.session_state.last_search = {"strict_groups": [], "fallback_keywords": []}
        st.rerun()

# --- MAIN LAYOUT (3 COLUMNS) ---
col1, col2, col3 = st.columns([2, 2.5, 2])

# --- COLUMN 1: CHAT INTERFACE ---
with col1:
    st.subheader("💬 AI Assistant")
    chat_container = st.container(height=550, border=True)

    # Display chat history with custom bubble styling
    for message in st.session_state.messages:
        # FIXED: Perform replace outside the f-string
        content_for_html = message["content"].replace("\n", "<br>")
        if message["role"] == "user":
            chat_container.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                    <div style="background-color: #DCF8C6; color: #000000; border-radius: 15px; padding: 10px 15px; max-width: 85%; word-wrap: break-word;">
                        {content_for_html}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            chat_container.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div style="background-color: #FFFFFF; color: #000000; border: 1px solid #E0E0E0; border-radius: 15px; padding: 10px 15px; max-width: 85%; word-wrap: break-word;">
                        {content_for_html}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )

# --- COLUMN 2: VISUALIZATIONS ---
with col2:
    st.subheader("📊 Visual Insights")
    with st.container(height=550, border=True):
        if not st.session_state.search_performed:
            st.info("Visualizations will appear here after you submit a prompt.")
        elif st.session_state.matched_data.empty:
            st.warning("No data found for your query. Please try another topic.")
        else:
            data_for_viz = st.session_state.matched_data.copy()

            display_data_context(data_for_viz, st.session_state.last_search)

            tabs = st.tabs([
                            "Summary", "Sentiment" ,"Engagement", "Trends", 
                            "Performance","🏆 Top Performers", "🗺️ Geospatial"
                            ])
            
            # --- VVV THIS ENTIRE BLOCK IS REVISED ---
            with tabs[0]: # Summary
                display_summary_metrics(data_for_viz)
                display_top_viral_posts(data_for_viz)
            
            with tabs[1]: # Sentiment
                plot_sentiment_distribution(data_for_viz)
            
            with tabs[2]: # Engagement
                plot_engagement_by_category(data_for_viz, category='TOPIK')
                plot_engagement_by_category(data_for_viz, category='GRUP')
            
            with tabs[3]: # Trends
                plot_time_series(data_for_viz)
                
            with tabs[4]: # Performance
                plot_followers_vs_engagement(data_for_viz)
                st.markdown("---") # Add a separator
                plot_performance_quadrant(data_for_viz)
            with tabs[5]: # Top Performers
                display_top_performers(data_for_viz)
            with tabs[6]: # Geospatial
                plot_geospatial_analysis(data_for_viz)
# --- ^^^ ADD THIS NEW BLOCK RIGHT AFTER IT ^^^ ---

# --- COLUMN 3: RAW DATA ---
with col3:
    st.subheader("📝 Raw Data")
    with st.container(height=550, border=True):
        display_raw_data_bubbles(st.session_state.matched_data)

# --- CHAT INPUT & PROCESSING ---
if prompt := st.chat_input("Ask about the data..."):
    # Add and display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    prompt_for_html = prompt.replace("\n", "<br>")
    chat_container.markdown(
        f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
            <div style="background-color: #DCF8C6; color: #000000; border-radius: 15px; padding: 10px 15px; max-width: 85%; word-wrap: break-word;">
                {prompt_for_html}
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # --- BACKEND LOGIC ---
    response_stream = None
    with st.spinner("Analyzing prompt..."):
        user_messages = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        previous_prompt = user_messages[-2] if len(user_messages) > 1 else ""
        analysis = classify_prompt_and_extract_entities(prompt, previous_prompt)

        prompt_type = analysis.get("type")
        dates = analysis.get("dates", [])


        # --- NEW LOGIC: If previous search failed, force next prompt to be a New Topic ---
        if st.session_state.matched_data.empty and len(st.session_state.messages) > 2:
            prompt_type = "New Topic"
            analysis = classify_prompt_and_extract_entities(prompt, "") # Re-analyze as a new topic
#
        
        # --- NEW ROBUST WORKFLOW ---
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

        # Otherwise, proceed with the normal search logic
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

            # Get AI response stream (now handles both cases)
            response_stream = get_ai_response(prompt, st.session_state.matched_data, st.session_state.last_search)

    # --- STREAM RESPONSE TO UI (This part is now universal) ---
    if response_stream:
        placeholder = chat_container.empty()
        full_response = ""
        for chunk in response_stream:
            full_response += chunk
            response_for_html = full_response.replace("\n", "<br>")
            placeholder.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div style="background-color: #FFFFFF; color: #000000; border: 1px solid #E0E0E0; border-radius: 15px; padding: 10px 15px; max-width: 85%; word-wrap: break-word;">
                        {response_for_html}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- UPDATE HISTORY & RERUN ---
    if prompt_type == "New Topic" and not st.session_state.matched_data.empty:
        history_summary = f"投 {prompt[:30]}..."
        st.session_state.history.append({
            "summary": history_summary, "messages": st.session_state.messages.copy(),
            "data": st.session_state.matched_data.copy(), "search_query": st.session_state.last_search.copy()
        })
    st.rerun()