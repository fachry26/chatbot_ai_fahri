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
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.6,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=80, b=200)  # extra bottom margin
    )
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

# --- NEW VISUALIZATION FUNCTIONS ---
# In visualizations.py, replace the old top performers functions with this one.

def display_top_performers(df):
    """Displays a tab with multiple top performer tables for key metrics."""
    st.subheader("🏆 Top Performers by Account")

    metrics_to_plot = {
        'FOLLOWERS': 'Top by Followers',
        'ENGAGEMENTS': 'Top by Engagements',
        'ESMR': 'Top by ESMR',
        'VIEWS': 'Top by Views',
        'LIKES': 'Top by Likes'
    }

    # Use columns for a more compact and readable layout
    col1, col2 = st.columns(2)
    
    # Split the list of metrics to display them across two columns
    metrics_list = list(metrics_to_plot.items())
    
    with col1:
        # Display the first 3 metrics in the left column
        for metric_col, title in metrics_list[:3]:
            if metric_col in df.columns:
                st.markdown(f"**{title}**")
                
                # Group by account, sum the metric, and get top 10
                top_df = df.groupby('AKUN')[metric_col].sum().nlargest(10).reset_index()
                total_metric = df[metric_col].sum()

                # Rename columns for clarity
                top_df.columns = ['Account', metric_col.title()]
                # Make the rank start from 1 instead of 0
                top_df.index = top_df.index + 1
                
                # Display the total and the table
                st.metric(label=f"Total {metric_col.title()}", value=f"{total_metric:,.0f}")
                st.dataframe(
                    top_df.style.format({metric_col.title(): '{:,.0f}'}), # Format numbers with commas
                    use_container_width=True
                )
                st.write("") # Add vertical space

    with col2:
        # Display the remaining metrics in the right column
        for metric_col, title in metrics_list[3:]:
            if metric_col in df.columns:
                st.markdown(f"**{title}**")
                
                top_df = df.groupby('AKUN')[metric_col].sum().nlargest(10).reset_index()
                total_metric = df[metric_col].sum()

                top_df.columns = ['Account', metric_col.title()]
                top_df.index = top_df.index + 1
                
                st.metric(label=f"Total {metric_col.title()}", value=f"{total_metric:,.0f}")
                st.dataframe(
                    top_df.style.format({metric_col.title(): '{:,.0f}'}),
                    use_container_width=True
                )
                st.write("") # Add vertical spac

# In visualizations.py, add this new function to the end of the file.

# In visualizations.py, replace the old plot_geospatial_analysis function with this new one.

def plot_geospatial_analysis(df):
    """Displays a more robust analysis for location and source data, including tables."""
    st.subheader("🗺️ Geospatial & Source Analysis")

    # --- 1. Locational Analysis ---
    if 'LOKASI' in df.columns and not df['LOKASI'].dropna().empty:
        location_counts = df['LOKASI'].value_counts().reset_index()
        location_counts.columns = ['LOKASI', 'Posts']
        
        # A dictionary to map major Indonesian provinces to coordinates for the bubble map
        indonesia_coords = {
            'DKI Jakarta': {'lat': -6.2088, 'lon': 106.8456}, 'Jawa Barat': {'lat': -6.9175, 'lon': 107.6191},
            'Jawa Tengah': {'lat': -7.1509, 'lon': 110.1403}, 'Jawa Timur': {'lat': -7.5361, 'lon': 112.2384},
            'Banten': {'lat': -6.4238, 'lon': 106.1662}, 'DI Yogyakarta': {'lat': -7.7956, 'lon': 110.3695},
            'Aceh': {'lat': 4.6951, 'lon': 96.7494}, 'Sumatera Utara': {'lat': 2.1154, 'lon': 99.5451},
            'Sumatera Barat': {'lat': -0.9471, 'lon': 100.3636}, 'Riau': {'lat': 0.5071, 'lon': 101.4478},
            'Jambi': {'lat': -1.6101, 'lon': 103.6131}, 'Sumatera Selatan': {'lat': -3.3194, 'lon': 103.9141},
            'Bengkulu': {'lat': -3.7928, 'lon': 102.2607}, 'Lampung': {'lat': -4.5586, 'lon': 105.4068},
            'Kalimantan Barat': {'lat': -0.0222, 'lon': 109.3443}, 'Kalimantan Tengah': {'lat': -1.6817, 'lon': 113.3824},
            'Kalimantan Selatan': {'lat': -3.0926, 'lon': 115.2838}, 'Kalimantan Timur': {'lat': 1.6406, 'lon': 116.4194},
            'Sulawesi Utara': {'lat': 1.4748, 'lon': 124.8421}, 'Sulawesi Tengah': {'lat': -1.4301, 'lon': 121.4456},
            'Sulawesi Selatan': {'lat': -3.6447, 'lon': 119.9424}, 'Sulawesi Tenggara': {'lat': -4.1449, 'lon': 122.1746},
            'Bali': {'lat': -8.4095, 'lon': 115.1889}, 'Nusa Tenggara Barat': {'lat': -8.6529, 'lon': 117.3616},
            'Nusa Tenggara Timur': {'lat': -8.6574, 'lon': 121.0794}, 'Maluku': {'lat': -3.2384, 'lon': 130.1453},
            'Papua': {'lat': -4.2699, 'lon': 138.0804}
        }
        
        # --- Robust Matching Logic ---
        # Create a normalized lookup dictionary (lowercase, no spaces)
        coords_lookup = {k.lower().replace(" ", ""): v for k, v in indonesia_coords.items()}
        
        def get_coords(location_name):
            if not isinstance(location_name, str): return None
            normalized_name = location_name.lower().replace(" ", "")
            return coords_lookup.get(normalized_name)

        # Apply the matching to get coordinates
        location_counts['coords'] = location_counts['LOKASI'].apply(get_coords)
        
        # Split into mapped and unmapped data for debugging and plotting
        mapped_df = location_counts.dropna(subset=['coords']).copy()
        unmapped_df = location_counts[location_counts['coords'].isna()]
        
        if not mapped_df.empty:
            mapped_df['lat'] = mapped_df['coords'].apply(lambda x: x['lat'])
            mapped_df['lon'] = mapped_df['coords'].apply(lambda x: x['lon'])

        # --- Display Table and Map side-by-side ---
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Top 10 Locations by Post Count**")
            top_10_table = location_counts[['LOKASI', 'Posts']].head(10)
            top_10_table.index = top_10_table.index + 1
            st.dataframe(top_10_table, use_container_width=True)

        with col2:
            if not mapped_df.empty:
                fig_map = px.scatter_geo(mapped_df, lat='lat', lon='lon', size='Posts',
                                         hover_name='LOKASI', projection="natural earth",
                                         scope='asia', center={'lat': -2.5, 'lon': 118},
                                         color='Posts', color_continuous_scale=px.colors.sequential.Plasma,
                                         hover_data={'Posts': ':,d', 'lat': False, 'lon': False})
                fig_map = apply_chart_style(fig_map, "Geographic Distribution of Posts")
                fig_map.update_layout(height=400)
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Could not map any locations from your data. Check names in the 'LOKASI' column.")
        
        # --- Optional Debugger ---
        with st.expander("View Data Mapping Info"):
            st.write("This section helps you see which locations were successfully found for the map.")
            st.markdown(f"**✅ Mapped Locations:** `{', '.join(mapped_df['LOKASI'].tolist())}`")
            if not unmapped_df.empty:
                st.markdown(f"**❌ Unmapped Locations:** `{', '.join(unmapped_df['LOKASI'].tolist())}`")

    else:
        st.info("No location data (LOKASI) available to display analysis.")

    st.markdown("---")

    # --- 2. Source Treemap (Unchanged) ---
    if 'SUMBER' in df.columns and not df['SUMBER'].dropna().empty:
        source_counts = df['SUMBER'].value_counts().reset_index()
        source_counts.columns = ['SUMBER', 'count']
        
        fig_treemap = px.treemap(source_counts, path=[px.Constant("All Sources"), 'SUMBER'], values='count',
                                 color='count', color_continuous_scale='Blues',
                                 hover_data={'count': ':,d'})
        fig_treemap.update_traces(textinfo="label+value", hovertemplate='<b>%{label}</b><br>Post Count: %{value}<extra></extra>')
        fig_treemap = apply_chart_style(fig_treemap, "Distribution by Media Source")
        fig_treemap.update_layout(height=400)
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("No source data (SUMBER) available to display treemap.")

# In visualizations.py, add this new function to the end of the file.

def plot_performance_quadrant(df):
    """
    Displays a quadrant analysis of accounts based on followers and engagement rate,
    and lists the top accounts in each quadrant.
    """
    st.subheader("Performance Quadrant Analysis")

    required_cols = ['AKUN', 'FOLLOWERS', 'ENGAGEMENTS', 'VIEWS']
    if not all(col in df.columns for col in required_cols) or df[required_cols].dropna().empty:
        st.info("Not enough data for Quadrant Analysis. Requires Account, Followers, Engagements, and Views.")
        return

    # --- 1. Data Preparation ---
    # Calculate Engagement Rate per post
    df_copy = df.copy()
    df_copy['ENGAGEMENT RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row['VIEWS'] if row['VIEWS'] > 0 else 0, axis=1
    )

    # Aggregate by account to get their average performance
    account_performance = df_copy.groupby('AKUN').agg(
        Avg_Followers=('FOLLOWERS', 'mean'),
        Avg_ER=('ENGAGEMENT RATE', 'mean')
    ).reset_index()

    if len(account_performance) < 4:
         st.info("Need at least 4 unique accounts to perform a quadrant analysis.")
         return

    # --- 2. Calculate Quadrant Boundaries (using median for robustness) ---
    median_followers = account_performance['Avg_Followers'].median()
    median_er = account_performance['Avg_ER'].median()

    # --- 3. Create the Scatter Plot ---
    fig = px.scatter(
        account_performance,
        x='Avg_Followers',
        y='Avg_ER',
        hover_name='AKUN',
        log_x=True, # Use log scale for followers to better visualize
        hover_data={'Avg_Followers': ':,.0f', 'Avg_ER': ':.2%'}
    )

    # Add quadrant lines and labels
    fig.add_vline(x=median_followers, line_dash="dash", line_color="grey")
    fig.add_hline(y=median_er, line_dash="dash", line_color="grey")
    fig.add_annotation(x=median_followers*1.1, y=median_er*1.1, text="<b>🏆 Champions</b><br>(High Followers, High ER)", showarrow=False, bgcolor="#d1fecb", borderpad=4)
    fig.add_annotation(x=median_followers*0.9, y=median_er*1.1, text="<b>💎 Hidden Gems</b><br>(Low Followers, High ER)", showarrow=False, xanchor='right', bgcolor="#ccf2ff", borderpad=4)
    fig.add_annotation(x=median_followers*0.9, y=median_er*0.9, text="<b>🌱 Niche Players</b><br>(Low Followers, Low ER)", showarrow=False, xanchor='right', yanchor='top', bgcolor="#fff5c0", borderpad=4)
    fig.add_annotation(x=median_followers*1.1, y=median_er*0.9, text="<b>📢 Megaphones</b><br>(High Followers, Low ER)", showarrow=False, yanchor='top', bgcolor="#ffddc7", borderpad=4)

    fig = apply_chart_style(fig, "Account Performance Quadrants")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # --- 4. Categorize and List Top Accounts ---
    def categorize_account(row):
        if row['Avg_Followers'] >= median_followers and row['Avg_ER'] >= median_er:
            return 'Champions'
        elif row['Avg_Followers'] < median_followers and row['Avg_ER'] >= median_er:
            return 'Hidden Gems'
        elif row['Avg_Followers'] < median_followers and row['Avg_ER'] < median_er:
            return 'Niche Players'
        else:
            return 'Megaphones'

    account_performance['Quadrant'] = account_performance.apply(categorize_account, axis=1)

    st.markdown("---")
    st.subheader("Top Accounts in Each Quadrant")

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        st.markdown("🏆 **Champions**")
        st.dataframe(
            account_performance[account_performance['Quadrant'] == 'Champions']
            .sort_values('Avg_ER', ascending=False).head(10)[['AKUN', 'Avg_ER']]
            .style.format({'Avg_ER': '{:.2%}'}), 
            use_container_width=True
        )
    with q2:
        st.markdown("💎 **Hidden Gems**")
        st.dataframe(
            account_performance[account_performance['Quadrant'] == 'Hidden Gems']
            .sort_values('Avg_ER', ascending=False).head(10)[['AKUN', 'Avg_ER']]
            .style.format({'Avg_ER': '{:.2%}'}), 
            use_container_width=True
        )
    with q3:
        st.markdown("📢 **Megaphones**")
        st.dataframe(
            account_performance[account_performance['Quadrant'] == 'Megaphones']
            .sort_values('Avg_Followers', ascending=False).head(10)[['AKUN', 'Avg_Followers']]
            .style.format({'Avg_Followers': '{:,.0f}'}), 
            use_container_width=True
        )
    with q4:
        st.markdown("🌱 **Niche Players**")
        st.dataframe(
            account_performance[account_performance['Quadrant'] == 'Niche Players']
            .sort_values('Avg_Followers', ascending=False).head(10)[['AKUN', 'Avg_Followers']]
            .style.format({'Avg_Followers': '{:,.0f}'}), 
            use_container_width=True
        )