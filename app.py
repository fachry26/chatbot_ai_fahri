# app.py

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components


from utils import (
    configure_fireworks, load_data, classify_prompt_and_extract_entities,
    search_data, get_ai_response, get_no_data_suggestion, get_contextual_chatter_response
)

from visualizations import (
    display_summary_metrics, plot_sentiment_distribution, plot_engagement_by_category,
    plot_time_series, plot_followers_vs_engagement, display_top_viral_posts,
    display_data_context, display_top_performers, plot_geospatial_analysis,
    plot_performance_quadrant, display_top_followers_posts,
    display_top_engagement_posts, plot_source_distribution
)

from components import (
    apply_custom_css, display_raw_data_bubbles, display_history, display_header_logo
)
import history_service

# --- PAGE CONFIG & SETUP ---
st.set_page_config(page_title="AI Social Media Dashboard", page_icon="logo_kurasi.png", layout="wide", initial_sidebar_state="expanded")

# Automatically scroll to top on rerun
components.html("<script>window.scrollTo(0, 0);</script>", height=0)

apply_custom_css()

# --- PERUBAHAN 2: Inisialisasi client Fireworks sekali saja dan muat data ---
# Inisialisasi client disimpan di session_state agar tidak dibuat ulang setiap kali ada interaksi
if "fireworks_client" not in st.session_state:
    st.session_state.fireworks_client = configure_fireworks()
df = load_data()


# ... (Pastikan session state ini diinisialisasi di bagian atas file Anda) ...
if "messages" not in st.session_state:
    st.session_state.messages = []
if "matched_data" not in st.session_state:
    st.session_state.matched_data = pd.DataFrame()
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False
if "last_search" not in st.session_state:
    st.session_state.last_search = {"strict_groups": [], "fallback_keywords": []}
# --- PERUBAHAN 1: Tambahkan state baru untuk "ingatan" ---
if "waiting_for_date" not in st.session_state:
    st.session_state.waiting_for_date = False

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
    background-color: #c7a4ff;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    width: 100%;
    text-align: left;
    }
    .new-chat-btn:hover {
    background-color: #b388ff;
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
# app.py

# --- COLUMN 1: CHAT INTERFACE ---
with col1:
    st.markdown(
        "<h3 style='display:flex; align-items:center; gap:8px; color:#2F5D9F;'>"
        "<i class='bi bi-robot'></i> AI Assistant</h3>",
        unsafe_allow_html=True
    )
    chat_container = st.container(height=550, border=True)
    
    # Menampilkan riwayat chat menggunakan komponen asli Streamlit
    for message in st.session_state.messages:
        # Tentukan avatar berdasarkan role
        if message["role"] == "user":
            avatar_img = "kur.png"  # Ganti dengan path logo Anda
        else:
            avatar_img = "ai.png"   # Ganti dengan path logo AI
        
        # Tampilkan bubble chat dengan avatar
        with chat_container.chat_message(message["role"], avatar=avatar_img):
            st.markdown(message["content"])

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
                display_top_engagement_posts(data_for_viz)
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
                st.markdown("---")
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
# app.py

# --- CHAT INPUT & SEQUENTIAL PROCESSING (VERSI FINAL & BERSIH) ---
if prompt := st.chat_input("Ask about the data..."):
    # 1. Tambahkan pesan pengguna ke state dan langsung tampilkan di UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user", avatar="kur.png"):
        st.markdown(prompt)

    # 2. Mulai proses di belakang layar untuk mendapatkan respons AI
    with st.spinner("Analyzing prompt and generating response..."):
        # Logika klasifikasi prompt Anda yang sudah benar (TIDAK DIUBAH)
        user_messages = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
        previous_prompt = user_messages[-2] if len(user_messages) > 1 else ""
        last_ai_response = ""
        if len(st.session_state.messages) > 1:
            for message in reversed(st.session_state.messages[:-1]):
                if message["role"] == "assistant":
                    last_ai_response = message["content"]
                    break
        
        analysis = classify_prompt_and_extract_entities(
            st.session_state.fireworks_client, prompt, previous_prompt, last_ai_response
        )
        prompt_type = analysis.get("type")
        dates = analysis.get("dates", [])
        
        # Logika "Safety Net" Anda (TIDAK DIUBAH)
        if st.session_state.waiting_for_date and prompt_type == "New Topic" and not dates:
            prompt_type = "Chatter"

        # 3. Siapkan generator respons berdasarkan tipe prompt dalam satu blok logika yang bersih
        response_generator = None
        if prompt_type == "New Topic":
            if not dates:
                st.session_state.waiting_for_date = True
                st.session_state.search_performed = False # Pastikan search flag mati
                def missing_date_response():
                    yield "Tentu, saya bisa carikan datanya. Mohon informasikan tanggal atau rentang tanggal spesifik yang Anda inginkan."
                response_generator = missing_date_response()
            else:
                st.session_state.waiting_for_date = False
                st.session_state.last_search = {"strict_groups": analysis.get("strict_groups", []), "fallback_keywords": analysis.get("fallback_keywords", [])}
                st.session_state.matched_data = search_data(df, st.session_state.last_search["strict_groups"], st.session_state.last_search["fallback_keywords"], dates)
                st.session_state.search_performed = True
                response_generator = get_ai_response(st.session_state.fireworks_client, prompt, st.session_state.matched_data, st.session_state.last_search)
        
        elif prompt_type == "Follow-Up":
            st.session_state.waiting_for_date = False
            if dates:
                st.session_state.matched_data = search_data(df, st.session_state.last_search["strict_groups"], st.session_state.last_search["fallback_keywords"], dates)
            st.session_state.search_performed = True
            response_generator = get_ai_response(st.session_state.fireworks_client, prompt, st.session_state.matched_data, st.session_state.last_search)

        elif prompt_type == "Chatter":
            st.session_state.waiting_for_date = False
            st.session_state.search_performed = False # Pastikan search flag mati
            response_generator = get_contextual_chatter_response(st.session_state.fireworks_client, st.session_state.messages)
    
    # 4. Stream respons AI ke UI dengan cara yang aman dan benar
    if response_generator:
        with chat_container.chat_message("assistant", avatar="ai.png"):
            full_response = st.write_stream(response_generator)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # 5. Rerun HANYA jika ada pencarian data yang berhasil, agar visualisasi di-update
        if st.session_state.search_performed:
             st.rerun()