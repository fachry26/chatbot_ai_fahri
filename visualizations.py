import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- GAYA VISUAL BARU ---

# 1. Palet warna kustom yang lebih modern dan cerah
COLOR_PALETTE = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# 2. Fungsi helper untuk menerapkan gaya konsisten ke semua grafik
def apply_chart_style(fig, title):
    """Menerapkan layout, font, dan warna yang konsisten pada grafik Plotly."""
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20, 'color': '#333A44'}
        },
        font={'family': 'Poppins', 'color': '#5D6D7E'},
        paper_bgcolor='rgba(255,255,255,0)', # Latar belakang transparan
        plot_bgcolor='rgba(255,255,255,0)',
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.25,
            'xanchor': 'center',
            'x': 0.5
        },
        margin=dict(t=80, b=80),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Poppins"
        )
    )
    # Menambahkan garis sumbu X dan Y yang lebih halus
    fig.update_xaxes(showline=True, linewidth=1, linecolor='#D6DBDF')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='#D6DBDF', gridcolor='#F2F3F4')
    return fig

# --- KONTEN KONTEKS BARU (TIDAK ADA PERUBAHAN) ---
# In visualizations.py

def display_data_context(df, search_query):
    """Displays the context of the current search, including topics and date range."""
    if df.empty:
        return

    strict_keywords = {kw for group in search_query.get('strict_groups', []) for kw in group}
    fallback_keywords = set(search_query.get('fallback_keywords', []))
    all_keywords = sorted(list(strict_keywords | fallback_keywords))
    
    min_date = df['TANGGAL PUBLIKASI'].min().strftime('%d %b %Y')
    max_date = df['TANGGAL PUBLIKASI'].max().strftime('%d %b %Y')
    date_display = min_date if min_date == max_date else f"{min_date} to {max_date}"

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🗓️ Data Range:**")
            # --- V CORRECTED LINE V ---
            st.markdown(f"<span style='font-size: 1.2em;'>{date_display}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**🔍 Data About:**")
            # --- V CORRECTED LINE V ---
            st.markdown(f"<span style='font-size: 1.2em;'>{', '.join(all_keywords)}</span>", unsafe_allow_html=True)
    st.write("")

# --- VISUALISASI YANG TELAH DIPERBARUI ---

def display_top_viral_posts(df):
    """Menampilkan 5 postingan paling viral dengan tata letak kartu yang lebih baik."""
    required_cols = ['ENGAGEMENTS', 'FOLLOWERS', 'AKUN', 'TOPIK', 'SENTIMEN', 'KONTEN']
    if df.empty or not all(col in df.columns for col in required_cols):
        st.info("No virality data to display.")
        return

    df_copy = df.copy()
    df_copy['VIRALITY RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row['FOLLOWERS'] if row['FOLLOWERS'] > 0 else 0,
        axis=1
    )

    st.subheader("🏆 Top 5 Viral Posts")
    top_posts = df_copy.sort_values(by='VIRALITY RATE', ascending=False).head(5)
    
    for _, row in top_posts.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**Post by: {row.get('AKUN', 'N/A')}**")
                st.caption(f"Topic: {row.get('TOPIK', 'N/A')} | Sentiment: {row.get('SENTIMEN', 'N/A')}")
                st.markdown(f"_{row.get('KONTEN', 'N/A')[:150]}..._")
            with col2:
                # --- V CITATION ADDED HERE V ---
                st.metric("Virality", f"{row['VIRALITY RATE']:.2%}", help="Calculated as (Engagements / Followers)")
                # --- ^ CITATION ADDED HERE ^ ---
                st.metric("Engagements", f"{row.get('ENGAGEMENTS', 0):,}")

def display_summary_metrics(df):
    """Menampilkan KPI cards dengan statistik ringkasan."""
    if df.empty:
        st.info("No data to display metrics.")
        return

    st.subheader("📊 Headline Stats")
    col1, col2, col3 = st.columns(3)

    total_posts = len(df)
    
    total_engagements = df['ENGAGEMENTS'].sum() if 'ENGAGEMENTS' in df.columns else 0
    total_views = df['VIEWS'].sum() if 'VIEWS' in df.columns else 0
    avg_engagement_rate = (total_engagements / total_views * 100) if total_views > 0 else 0
    
    col1.metric("Total Posts", f"{total_posts:,}")
    # --- V CITATION ADDED HERE V ---
    col2.metric("Avg. Engagement Rate", f"{avg_engagement_rate:.2f}%", help="Calculated as (Total Engagements / Total Views) * 100")
    # --- ^ CITATION ADDED HERE ^ ---
    col3.metric("Total Views", f"{total_views:,}")

# In visualizations.py, replace the old function with this one

# In visualizations.py, replace the old function with this new one.

def plot_sentiment_distribution(df):
    """Donut chart untuk distribusi sentimen."""
    if df.empty or 'SENTIMEN' not in df.columns:
        st.info("No sentiment data available.")
        return
    
    # --- V FINAL, MORE ROBUST FIX V ---
    # 1. Get value counts and explicitly name the new 'count' column upon creation.
    #    This results in a DataFrame with columns: ['index', 'count']
    sentiment_counts = df['SENTIMEN'].value_counts().reset_index(name='count')
    
    # 2. Now, safely rename the 'index' column to 'SENTIMEN'.
    #    This results in a DataFrame with columns: ['SENTIMEN', 'count']
    sentiment_counts = sentiment_counts.rename(columns={'index': 'SENTIMEN'})
    # --- ^ FINAL, MORE ROBUST FIX ^ ---

    fig = px.pie(sentiment_counts, names='SENTIMEN', values='count', 
                 hole=0.4, color_discrete_sequence=COLOR_PALETTE)
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label', 
        hovertemplate="<b>%{label}</b><br>Total Posts: %{value}<br>Persentase: %{percent}<extra></extra>"
    )
    
    fig = apply_chart_style(fig, "Distribusi Sentimen Publik")
    st.plotly_chart(fig, use_container_width=True)

def plot_engagement_by_category(df, category='TOPIK'):
    """Bar chart untuk engagement dengan label data dan format persentase."""
    required_cols = [category, 'ENGAGEMENTS', 'VIEWS']
    if df.empty or not all(col in df.columns for col in required_cols):
        st.info(f"Not enough data to plot engagement by {category}.")
        return

    df_copy = df.copy()
    df_copy['ENGAGEMENT RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row['VIEWS'] if row['VIEWS'] > 0 else 0,
        axis=1
    )
    
    engagement_by_cat = df_copy.groupby(category)['ENGAGEMENT RATE'].mean().sort_values(ascending=False).reset_index()
    
    fig = px.bar(engagement_by_cat, x=category, y='ENGAGEMENT RATE',
                 color=category, color_discrete_sequence=COLOR_PALETTE,
                 text_auto='.2%')
    
    fig.update_traces(textposition='outside')
    fig.update_yaxes(title='Average Engagement Rate', tickformat='.2%')
    fig.update_xaxes(title=category)
    
    fig = apply_chart_style(fig, f'Rata-Rata Engagement Rate per {category}')
    st.plotly_chart(fig, use_container_width=True)
    # --- V CITATION ADDED HERE V ---
    st.caption("ⓘ Engagement Rate is calculated as Engagements / Views.")
    # --- ^ CITATION ADDED HERE ^ ---

def plot_time_series(df):
    """Area chart untuk tren posting dari waktu ke waktu."""
    if df.empty or 'TANGGAL PUBLIKASI' not in df.columns:
        st.info("No time series data available.")
        return
    
    df['TANGGAL PUBLIKASI'] = pd.to_datetime(df['TANGGAL PUBLIKASI'])
    posts_over_time = df.set_index('TANGGAL PUBLIKASI').resample('D').size().reset_index(name='count')
    
    fig = px.area(posts_over_time, x='TANGGAL PUBLIKASI', y='count',
                  labels={'TANGGAL PUBLIKASI': 'Tanggal', 'count': 'Jumlah Post'},
                  markers=True)
    
    fig.update_traces(line=dict(color=COLOR_PALETTE[1], width=2))
    
    fig = apply_chart_style(fig, 'Tren Jumlah Post Harian')
    st.plotly_chart(fig, use_container_width=True)

def plot_followers_vs_engagement(df):
    """Scatter plot dengan gaya dan tooltip yang lebih informatif."""
    required_cols = ['FOLLOWERS', 'ENGAGEMENTS', 'VIEWS', 'SENTIMEN', 'AKUN']
    if df.empty or not all(col in df.columns for col in required_cols):
        st.info("Not enough data for scatter plot.")
        return

    df_copy = df.copy()
    df_copy['ENGAGEMENT RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row['VIEWS'] if row['VIEWS'] > 0 else 0,
        axis=1
    )
    
    fig = px.scatter(df_copy, x='FOLLOWERS', y='ENGAGEMENT RATE',
                     size='ENGAGEMENTS', color='SENTIMEN', 
                     hover_name='AKUN',
                     log_x=True,
                     color_discrete_map={
                         'Positive': COLOR_PALETTE[2],
                         'Negative': COLOR_PALETTE[3],
                         'Neutral': COLOR_PALETTE[7]
                     },
                     hover_data={
                         'FOLLOWERS': ':,',
                         'ENGAGEMENT RATE': ':.2%',
                         'ENGAGEMENTS': ':,'
                     })
    
    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')), selector=dict(mode='markers'))
    
    fig = apply_chart_style(fig, 'Followers vs. Engagement Rate')
    fig.update_layout(hovermode='closest')
    st.plotly_chart(fig, use_container_width=True)
    # --- V CITATION ADDED HERE V ---
    st.caption("ⓘ Engagement Rate is calculated as Engagements / Views.")
    # --- ^ CITATION ADDED HERE ^ ---