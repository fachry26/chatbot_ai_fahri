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
    plot_time_series, plot_followers_vs_engagement, display_top_viral_posts
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

# --- COLUMN 2 & 3 (No changes here) ---
with col2:
    st.subheader("📊 Visual Insights")
    with st.container(height=550, border=True):
        if not st.session_state.search_performed:
            st.info("Visualizations will appear here after you submit a prompt.")
        elif st.session_state.matched_data.empty:
            st.warning("No data found for your query. Please try another topic.")
        else:
            data_for_viz = st.session_state.matched_data.copy()
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Sentiment", "Engagement", "Trends", "Virality"])
            with tab1: display_summary_metrics(data_for_viz); display_top_viral_posts(data_for_viz)
            with tab2: plot_sentiment_distribution(data_for_viz)
            with tab3: plot_engagement_by_category(data_for_viz, category='TOPIK'); plot_engagement_by_category(data_for_viz, category='JENIS AKUN')
            with tab4: plot_time_series(data_for_viz)
            with tab5: plot_followers_vs_engagement(data_for_viz)
with col3:
    st.subheader("📝 Raw Data")
    with st.container(height=550, border=True):
        display_raw_data_bubbles(st.session_state.matched_data)


# --- CHAT INPUT & PROCESSING ---
if prompt := st.chat_input("Ask about the data..."):
    # Add and display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    # FIXED: Perform replace outside the f-string
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

    # Backend logic
    with st.spinner("Analyzing prompt..."):
        user_messages = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        previous_prompt = user_messages[-2] if len(user_messages) > 1 else ""
        analysis = classify_prompt_and_extract_entities(prompt, previous_prompt)
        prompt_type = analysis.get("type")
        dates = analysis.get("dates", [])

        if prompt_type == "New Topic":
            strict_groups = analysis.get("strict_groups", [])
            fallback_keywords = analysis.get("fallback_keywords", [])
            st.session_state.last_search = {"strict_groups": strict_groups, "fallback_keywords": fallback_keywords}
            st.session_state.matched_data = search_data(df, strict_groups, fallback_keywords, dates)
        elif prompt_type == "Follow-Up" and dates:
            last_search_params = st.session_state.last_search
            st.session_state.matched_data = search_data(df, last_search_params["strict_groups"], last_search_params["fallback_keywords"], dates)
        st.session_state.search_performed = True

    # Get AI response and stream it with custom styling
    response_stream = get_ai_response(prompt, st.session_state.matched_data) if not st.session_state.matched_data.empty else get_no_data_suggestion(prompt)
    
    placeholder = chat_container.empty()
    full_response = ""
    for chunk in response_stream:
        full_response += chunk
        # FIXED: Perform replace outside the f-string
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

    # Add final AI response to session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Update history and rerun to refresh other columns
    if prompt_type == "New Topic" and not st.session_state.matched_data.empty:
        history_summary = f"📊 {prompt[:30]}..."
        st.session_state.history.append({
            "summary": history_summary, "messages": st.session_state.messages.copy(),
            "data": st.session_state.matched_data.copy(), "search_query": st.session_state.last_search.copy()
        })
    st.rerun()