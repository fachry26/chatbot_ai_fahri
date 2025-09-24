import streamlit as st
import pandas as pd
import math
from datetime import datetime
import history_service # <-- This import was already in the original code

# Di file components.py

def apply_custom_css():
    st.markdown("""
        
        <style>
        /* --- LANGKAH 1: Tambahkan Icon Library Profesional (Boxicons) --- */
        @import url('https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css');
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css');
        
        /* --- [START] ADDED CSS FOR BUBBLE CARDS --- */
        .sentiment-card {
            background-color: #ffffff;
            border-left: 5px solid #6c757d; /* Default neutral color */
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            font-family: 'Poppins', sans-serif;
        }

        .sentiment-card.positive-card {
            border-left-color: #10B981; /* Green for positive */
        }

        .sentiment-card.negative-card {
            border-left-color: #EF4444; /* Red for negative */
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #6c757d;
            padding-bottom: 8px;
            margin-bottom: 8px;
            border-bottom: 1px solid #e9ecef;
        }

        .card-author {
            font-weight: 600;
            color: #343a40;
        }

        .card-content {
            font-size: 0.95em;
            line-height: 1.5;
            color: #212529;
            padding: 5px 0;
        }

        .card-metrics {
            display: flex;
            justify-content: space-around;
            text-align: center;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e9ecef;
        }

        .metric-value {
            font-size: 1.1em;
            font-weight: 600;
            color: #000000;
        }

        .metric-label {
            font-size: 0.8em;
            color: #6c757d;
            text-transform: uppercase;
        }
        /* --- [END] ADDED CSS FOR BUBBLE CARDS --- */
        
        /* --- Style Helper untuk Ikon Baru --- */
        .icon {
            vertical-align: middle;
            font-size: 1.3em; /* Ukuran ikon sedikit lebih besar dari teks */
            margin-right: 8px; /* Jarak antara ikon dan teks */
        }
                
        .stIconMaterial{font-family: 'Material Symbols Rounded' ;}
        .icon-blue { color: #3B82F6; }
        .icon-green { color: #10B981; }
        .icon-orange { color: #F97316; }

        /* HIDE default Streamlit UI elements */
        iframe[title="streamlit_app_deploy_button"] {display: none;}
        [data-testid="stAppToolbar"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbarActions"] {display: none !important;}
        [data-testid="stSidebarHeader"] {display: none !important;}
        [data-testid="stIFrame"] {display: none !important;}
        [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F0F2FF 0%, #E0E7FF 100%);
        }
                
        [data-testid="stSidebarContent"] {
        background: linear-gradient(to bottom,
  #ffffff 0%,
  #ffffff 40%,
  #7daedc 70%,   /* biru lembut */
  #5a4e8c 100%   /* ungu lembut */
);

        border-radius: 10px;       /* Sudut membulat agar sesuai dengan sidebar */
        padding: 15px;             /* Jarak di dalam area konten */
        margin-top: 15px;          /* Jarak dari judul di atasnya */
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05); /* Bayangan ke dalam yang halus */
        }


        
                /* Chat bubbles */
        .chat-bubble {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            margin: 6px 0;
            font-size: 0.95em;
            line-height: 1.4;
            word-wrap: break-word;
            font-family: 'Poppins', sans-serif;
        }

        /* Human prompt (kanan, hijau WhatsApp) */
        .chat-human {
            background-color: #DCF8C6;
            margin-left: auto;
            margin-right: 0;
            text-align: left;
        }

        /* AI response (kiri, oranye muda) */
        .chat-ai {
            background-color: #FFE5B4;
            margin-right: auto;
            margin-left: 0;
            text-align: left;
        }

    
                

        html, body, [class*="st-"], [data-testid*="st-"] {
            font-size: 13px;
            font-family: 'Poppins', sans-serif;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff ;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) ;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 20px 15px ;
        }
        .sidebar-title {
        margin-bottom: 6px;
    }
    .main-title {
        font-weight: 600;
        font-size: 20px;
        color: #2F5D9F;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sub-title {
        font-weight: 400;
        font-size: 16px;
        color: #444;
    }
    

        /* Custom button layout (two-column buttons) */
        [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] div:nth-child(1) [data-testid="stButton"] button {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            color: #212529;
            text-align: left;
            height: 75px; 
            white-space: normal;
            line-height: 1.4;
            padding: 10px 12px ;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border-top-right-radius: 0px ;
            border-bottom-right-radius: 0px ;
            font-size: 12px ;
        }
        [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] div:nth-child(1) [data-testid="stButton"] button i {
            font-size: 0.9em;
            color: #6c757d;
        }
        [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] div:nth-child(2) [data-testid="stButton"] button {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-left: none; 
            color: #6c757d;
            height: 75px;
            width: 50px ;
            border-top-left-radius: 0px ;
            border-bottom-left-radius: 0px ;
        }
        [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] div:nth-child(2) [data-testid="stButton"] button:hover {
            color: #dc3545;
            background-color: #f8d7da;
        }
        </style>
    """, unsafe_allow_html=True)


def apply_chatinput_css():
    st.markdown("""
    <style>
    /* Wrapper chat input */
    [data-testid="stChatInput"] {
        background-color: #f0f2f5 !important;  /* mirip WhatsApp input */
        border: 1px solid #d1d5db !important;
        border-radius: 20px !important;
        padding: 8px 12px !important;
    }

    /* Textarea styling */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] [data-baseweb="textarea"] {
        background-color: transparent !important;
        color: #111827 !important;      /* teks hitam */
        font-size: 15px !important;
    }

    /* Placeholder biar lebih jelas */
    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInput"] [data-baseweb="textarea"]::placeholder {
        color: #6b7280 !important;      /* abu-abu sedang */
        opacity: 1 !important;
    }

    /* Tombol kirim (panah) */
    [data-testid="stChatInput"] button {
        color: #3B82F6 !important;      /* biru */
    }
    </style>
    """, unsafe_allow_html=True)


def display_raw_data_bubbles(df):
    if df.empty:
        st.info("Belum ada data untuk ditampilkan. Silakan lakukan pencarian terlebih dahulu.")
        return

    # Safeguard: Ensure date column is in datetime format.
    if 'TANGGAL PUBLIKASI' in df.columns:
        df['TANGGAL PUBLIKASI'] = pd.to_datetime(df['TANGGAL PUBLIKASI'], errors='coerce')
        df.dropna(subset=['TANGGAL PUBLIKASI'], inplace=True)

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
        selected_sentiments = st.multiselect("Filter by Sentiment", options=unique_sentiments)
    with filter_col2:
        unique_topics = df_with_virality['TOPIK'].unique() if 'TOPIK' in df_with_virality.columns else []
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
        # --- ICON CHANGE: Replaced emoji with Streamlit icon shortcode ---
        if prev_col.button(":arrow_left: Previous", use_container_width=True, disabled=(st.session_state.current_page == 0)):
            st.session_state.current_page -= 1
            st.rerun()
        page_col.write(f"<div style='text-align: center;'>Page {st.session_state.current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        # --- ICON CHANGE: Replaced emoji with Streamlit icon shortcode ---
        if next_col.button("Next :arrow_right:", use_container_width=True, disabled=(st.session_state.current_page >= total_pages - 1)):
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

        # GANTI BLOK KODE LAMA ANDA DENGAN YANG INI
        html_card = f"""
        <div class="sentiment-card {sentiment}-card">
            <div class="card-header">
                <div class="card-author">:bust_in_silhouette: {row.get('AKUN', 'N/A')}</div>
                <div class="card-date">:date: {date_str}</div>
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
    st.image("logo_ai.png", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.image("logo_setneg.png", width=60)
    with col2:
        st.image("logo_kurasi.png", width=60)
    st.markdown(
        "<div class='sidebar-title main-title'>Chatbot AI Media Monitoring</div> <div class='sidebar-title sub-title'>Kementerian Sekretariat Negara Republik Indonesia</div> <div class='sidebar-title period-title'>Data April s.d September 2025</div>", 
        unsafe_allow_html=True
    )
 
from collections import defaultdict

def display_history():
    history_list = history_service.load_chat_sessions()

    if not history_list:
        st.markdown(
            "<div style='text-align:center; color:#888; font-style:italic;'>No recent chats</div>",
            unsafe_allow_html=True
        )
        return

    grouped_history = defaultdict(list)
    today = datetime.now().date()

    for item in history_list:
        dt_object = datetime.fromisoformat(item['timestamp'])
        if dt_object.date() == today:
            grouped_history["HARI INI"].append(item)
        else:
            grouped_history[dt_object.strftime("%B %Y")].append(item)

    # CSS card
    st.markdown("""
        <style>
        .history-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .history-card:hover {
            background: #eef2f7;
        }
        .history-title {
            font-size: 14px;
            font-weight: 500;
            margin: 0;
        }
        .history-details {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .icon-btn > button {
            background: none !important;
            border: none !important;
                border-radius:10px !important;
            color: #888 !important;
            font-size: 16px !important;
            padding: 0 !important;
        }
        .icon-btn > button:hover {
            color: #d9534f !important;
        }
        .full-btn > button {
            background: none !important;
            border-radius:10px !important;
            text-align: left !important;
            padding: 0 !important;
            color: inherit !important;
        }
        </style>
    """, unsafe_allow_html=True)

    for group_name, items in grouped_history.items():
        st.caption(group_name.upper())
        for item in items:
            session_id = item['id']
            dt_object = datetime.fromisoformat(item['timestamp'])
            date_str = dt_object.strftime("%d %b")
            time_str = dt_object.strftime("%H.%M")
            msg_count = f"{item['message_count']} pesan"
            details = f"{date_str} • {time_str} • {msg_count}"

            col1, col2 = st.columns([8, 1])
            with col1:
                if st.button(
                    f"💬 {item['summary']}\n\n{details}",
                    key=f"load_{session_id}",
                    help="Load chat"
                ):
                    session_data = history_service.load_specific_session(session_id)
                    if session_data:
                        st.session_state.messages = session_data["messages"]
                        st.session_state.matched_data = session_data["matched_data"]
                        st.session_state.last_search = session_data["last_search"]
                        st.session_state.search_performed = session_data["search_performed"]
                        st.rerun()

            with col2:
                if st.button("🗑", key=f"delete_{session_id}", help="Delete chat"):
                    history_service.delete_chat_session(session_id)
                    st.rerun()
