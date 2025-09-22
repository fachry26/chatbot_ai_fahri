# components.py

import streamlit as st
import pandas as pd
import math

def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        .stApp{
            background: linear-gradient(182deg, #f8f7fa, #eeecfd);
        }
        html, body, [class*="st-"], [data-testid*="st-"] {
            font-family: 'Roboto', sans-serif !important;
            font-size: 13px;
        }

        /* --- STYLE FOR THE CHAT INPUT AREA --- */
        [data-testid="stForm"] {
            background-color: #FFFFFF;
            border-top: 1px solid #E5E5E5;
            padding: 8px 16px;
        }
                
                #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.stMainBlockContainer.block-container.st-emotion-cache-liupih.e4man114 > div > div:nth-child(1){
                    display: none;
                }
                
        .stChatInput {
                border-radius: 21px !important;
                border: 1px solid blue !important;
                }

        .sentiment-card {
            border-radius: 10px; padding: 15px; margin-bottom: 15px;
            border: 1px solid #e0e0e0; border-left-width: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: all 0.3s ease-in-out;
        }
        .sentiment-card:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); transform: translateY(-2px);
        }
        .positive-card { border-left-color: #28a745; }
        .negative-card { border-left-color: #dc3545; }
        .neutral-card { border-left-color: #6c757d; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .card-author { font-weight: 600; color: #333; }
        .card-date { font-size: 0.8rem; color: #888; }
        .card-content { font-size: 0.95rem; color: #555; margin-bottom: 15px; }
        .card-metrics { display: flex; justify-content: space-around; text-align: center; }
        .metric-value { font-size: 1.1rem; font-weight: 600; }
        .metric-label { font-size: 0.75rem; color: #888; }
        [data-testid="stHorizontalBlock"] > div:not(:last-child) {
            border-right: 1px solid rgba(211, 211, 211, 0.5); padding-right: 25px;
        }
        [data-testid="stHorizontalBlock"] > div:not(:first-child) {
            padding-left: 25px;
        }
        .block-container { padding-top: 2rem; }
        
        /* --- SIDEBAR --- */
        .stSidebar {
            background-color: #ffffff !important;
            box-shadow: 1px 0px 10px rgba(0,0,0,0.1);
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 20px 15px !important;
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            text-align: center;
            margin: 15px 0 20px 0;
        }
        .stImageContainer {width: 200%; max-width: 200%;    margin: 0 auto;!important;}
        
        div[data-testid="stVerticalBlock"] > div.stColumn {
            background-color: #fff;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        .stAppHeader{
            background: rgba(0,0,0,0) !important;
        }
                
                *[data-testid="stIconMaterial"] {
                font-family: "Material Symbols Rounded" !important;
            }
                
        .stBottom > div{
                background: rgba(0,0,0,0) !important;
        }
                
                div.stAppDeployButton, span.stMainMenu {
                    display: none;
                }
        </style>
    """, unsafe_allow_html=True)

# ... sisa kode di components.py tetap sama ...
# (display_raw_data_bubbles, display_header_logo, display_history)

# In components.py, replace the display_raw_data_bubbles function.

# Di file components.py

def display_raw_data_bubbles(df):
    if df.empty:
        st.info("No raw data to display.")
        return

    df_with_virality = df.copy()
    if 'ENGAGEMENTS' in df_with_virality.columns and 'FOLLOWERS' in df_with_virality.columns:
        df_with_virality['VIRALITY RATE'] = df_with_virality.apply(
            lambda row: row['ENGAGEMENTS'] / row['FOLLOWERS'] if row['FOLLOWERS'] > 0 else 0, axis=1
        )
    else:
        df_with_virality['VIRALITY RATE'] = 0

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        unique_sentiments = df_with_virality['SENTIMEN'].unique() if 'SENTIMEN' in df_with_virality.columns else []
        # --- FIX: Changed st.multoselect to st.multiselect ---
        selected_sentiments = st.multiselect("Filter by Sentiment", options=unique_sentiments)
    with filter_col2:
        unique_topics = df_with_virality['TOPIK'].unique() if 'TOPIK' in df_with_virality.columns else []
        # --- FIX: Changed st.multoselect to st.multiselect ---
        selected_topics = st.multiselect("Filter by Topic", options=unique_topics)

    filtered_df = df_with_virality.copy()
    if selected_sentiments:
        filtered_df = filtered_df[filtered_df['SENTIMEN'].isin(selected_sentiments)]
    if selected_topics:
        filtered_df = filtered_df[filtered_df['TOPIK'].isin(selected_topics)]

    ITEMS_PER_PAGE = 20
    total_items = len(filtered_df)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 0

    if total_items > 0 and st.session_state.current_page >= total_pages:
        st.session_state.current_page = 0

    start_idx = st.session_state.current_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_df = filtered_df.iloc[start_idx:end_idx]

    st.caption(f"Showing {len(paginated_df)} of {total_items} posts")

    if total_pages > 1:
        prev_col, page_col, next_col = st.columns([2, 3, 2])
        if prev_col.button("⬅️ Previous", use_container_width=True, disabled=(st.session_state.current_page == 0)):
            st.session_state.current_page -= 1
            st.rerun()
        page_col.write(f"<div style='text-align: center;'>Page {st.session_state.current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        if next_col.button("Next ➡️", use_container_width=True, disabled=(st.session_state.current_page >= total_pages - 1)):
            st.session_state.current_page += 1
            st.rerun()
    st.write("---")

    if paginated_df.empty:
        st.warning("No posts match the current filter criteria.")

    for _, row in paginated_df.iterrows():
        sentiment = str(row.get('SENTIMEN', 'Neutral')).lower()
        content = str(row.get('KONTEN', 'N/A')).replace("<", "&lt;").replace(">", "&gt;")
        date_val = row.get('TANGGAL PUBLIKASI', pd.NaT)
        date_str = date_val.strftime('%d %b %Y') if pd.notna(date_val) else "N/A"

        html_card = f"""
        <div class="sentiment-card {sentiment}-card">
            <div class="card-header">
                <div class="card-author">👤 {row.get('AKUN', 'N/A')}</div>
                <div class="card-date">🗓️ {date_str}</div>
            </div>
            <div class="card-content">{content}</div>
            <div class="card-metrics">
                <div>
                    <div class="metric-value">{row.get('ENGAGEMENTS', 0):,}</div>
                    <div class="metric-label">ENGAGEMENTS</div>
                </div>
                <div>
                    <div class="metric-value">{row.get('TOPIK', 'N/A')}</div>
                    <div class="metric-label">TOPIC</div>
                </div>
                <div>
                    <div class="metric-value">{row.get('VIRALITY RATE', 0):.2%}</div>
                    <div class="metric-label">VIRALITY</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

def display_header_logo():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("logo_setneg.png", width=30)
    with col2:
        st.image("logo_ai.png", width=30)
    with col3:
        st.image("logo_kurasi.png", width=30)

    st.markdown("<div class='sidebar-title'>Social Media AI</div>", unsafe_allow_html=True)

def display_history(history_list):
    if not history_list:
        st.markdown("<div style='text-align:center; color:#888; font-style:italic;'>No recent chat</div>", unsafe_allow_html=True)
        return
    for i, item in enumerate(history_list):
        if st.button(item["summary"], key=f"history_{i}", use_container_width=True):
            st.session_state.messages = item["messages"]