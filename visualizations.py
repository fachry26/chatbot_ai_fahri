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

# --- VISUALISASI YANG TELAH DISEMPURNAKAN ---

def display_top_viral_posts(df):
    """Menampilkan 5 postingan paling viral dengan tata letak kartu yang lebih baik."""
    if df.empty or 'VIRALITY RATE' not in df.columns:
        st.info("No virality data to display.")
        return
        
    st.subheader("🏆 Top 5 Viral Posts")
    top_posts = df.sort_values(by='VIRALITY RATE', ascending=False).head(5)
    
    for _, row in top_posts.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**Post by: {row.get('AKUN', 'N/A')}**")
                st.caption(f"Topic: {row.get('TOPIK', 'N/A')} | Sentiment: {row.get('SENTIMEN', 'N/A')}")
                st.markdown(f"_{row.get('KONTEN', 'N/A')[:150]}..._")
            with col2:
                st.metric("Virality", f"{row['VIRALITY RATE']:.2%}")
                st.metric("Engagements", f"{row.get('ENGAGEMENTS', 0):,}")

def display_summary_metrics(df):
    """Menampilkan KPI cards dengan statistik ringkasan (tidak berubah)."""
    if df.empty:
        st.info("No data to display metrics.")
        return
        
    st.subheader("📊 Headline Stats")
    col1, col2, col3 = st.columns(3)
    
    total_posts = len(df)
    avg_engagement_rate = df['ENGAGEMENT RATE'].mean() * 100 if 'ENGAGEMENT RATE' in df.columns else 0
    total_impressions = df['IMPRESSION'].sum() if 'IMPRESSION' in df.columns else 0
    
    col1.metric("Total Posts", f"{total_posts:,}")
    col2.metric("Avg. Engagement Rate", f"{avg_engagement_rate:.2f}%")
    col3.metric("Total Impressions", f"{total_impressions:,}")

def plot_sentiment_distribution(df):
    """Donut chart untuk distribusi sentimen dengan label yang lebih baik."""
    if df.empty or 'SENTIMEN' not in df.columns:
        st.info("No sentiment data available.")
        return
    sentiment_counts = df['SENTIMEN'].value_counts().reset_index()
    sentiment_counts.columns = ['SENTIMEN', 'count']
    
    fig = px.pie(sentiment_counts, names='SENTIMEN', values='count', 
                 hole=0.4, color_discrete_sequence=COLOR_PALETTE)
    
    # Memperbarui tampilan label dan tooltip
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label', 
        hovertemplate="<b>%{label}</b><br>Total Posts: %{value}<br>Persentase: %{percent}<extra></extra>"
    )
    
    fig = apply_chart_style(fig, "Distribusi Sentimen Publik")
    st.plotly_chart(fig, use_container_width=True)

def plot_engagement_by_category(df, category='TOPIK'):
    """Bar chart untuk engagement dengan label data dan format persentase."""
    if df.empty or category not in df.columns or 'ENGAGEMENT RATE' not in df.columns:
        st.info(f"Not enough data to plot engagement by {category}.")
        return
    
    engagement_by_cat = df.groupby(category)['ENGAGEMENT RATE'].mean().sort_values(ascending=False).reset_index()
    
    fig = px.bar(engagement_by_cat, x=category, y='ENGAGEMENT RATE',
                 color=category, color_discrete_sequence=COLOR_PALETTE,
                 text_auto='.2%') # Menambahkan label data dengan format persen
    
    fig.update_traces(textposition='outside')
    fig.update_yaxes(title='Average Engagement Rate', tickformat='.2%') # Format sumbu Y
    fig.update_xaxes(title=category)
    
    fig = apply_chart_style(fig, f'Rata-Rata Engagement Rate per {category}')
    st.plotly_chart(fig, use_container_width=True)

# In visualizations.py

def plot_time_series(df):
    """Area chart untuk tren posting dari waktu ke waktu."""
    # CORRECTED THE COLUMN NAME HERE TO ALL UPPERCASE
    if df.empty or 'TANGGAL PUBLIKASI' not in df.columns:
        st.info("No time series data available.")
        return
    
    posts_over_time = df.set_index('TANGGAL PUBLIKASI').resample('D').size().reset_index(name='count')
    
    fig = px.area(posts_over_time, x='TANGGAL PUBLIKASI', y='count',
                  labels={'TANGGAL PUBLIKASI': 'Tanggal', 'count': 'Jumlah Post'},
                  markers=True)
    
    fig.update_traces(line=dict(color=COLOR_PALETTE[1], width=2))
    
    fig = apply_chart_style(fig, 'Tren Jumlah Post Harian')
    st.plotly_chart(fig, use_container_width=True)

def plot_followers_vs_engagement(df):
    """Scatter plot dengan gaya dan tooltip yang lebih informatif."""
    if df.empty or 'FOLLOWERS' not in df.columns or 'ENGAGEMENT RATE' not in df.columns:
        st.info("Not enough data for scatter plot.")
        return
    
    fig = px.scatter(df, x='FOLLOWERS', y='ENGAGEMENT RATE',
                     size='ENGAGEMENTS', color='SENTIMEN', 
                     hover_name='AKUN',
                     log_x=True,
                     color_discrete_map={
                         'Positive': COLOR_PALETTE[2],
                         'Negative': COLOR_PALETTE[3],
                         'Neutral': COLOR_PALETTE[7]
                     },
                     hover_data={ # Kustomisasi data saat hover
                         'FOLLOWERS': ':,',
                         'ENGAGEMENT RATE': ':.2%',
                         'ENGAGEMENTS': ':,'
                     })
    
    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')), selector=dict(mode='markers'))
    
    fig = apply_chart_style(fig, 'Followers vs. Engagement Rate')
    fig.update_layout(hovermode='closest')
    st.plotly_chart(fig, use_container_width=True)