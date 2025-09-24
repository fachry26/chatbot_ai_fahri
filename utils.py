# utils.py

import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import time

def configure_openai():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        st.error("OpenAI API key not found. Please create a .env file with your key.")
        st.stop()

@st.cache_data
def load_data(file_path="data_full.xlsx"):
    """Memuat, membersihkan, dan menyiapkan dataset."""
    try:
        df = pd.read_excel(file_path)

        # PASTIKAN KONVERSI TANGGAL ROBUST
        # 'errors='coerce'' akan mengubah tanggal yang tidak valid menjadi NaT (Not a Time)
        df['TANGGAL PUBLIKASI'] = pd.to_datetime(df['TANGGAL PUBLIKASI'], errors='coerce')

        # Hapus baris yang tanggalnya gagal dikonversi untuk menjaga integritas data
        df.dropna(subset=['TANGGAL PUBLIKASI'], inplace=True)

        # Pastikan kolom numerik penting diperlakukan sebagai angka
        numeric_cols = ['FOLLOWERS', 'ENGAGEMENTS', 'REACTIONS', 'COMMENTS', 'SHARES', 'VIEWS']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except FileNotFoundError:
        st.error(f"Error: File {file_path} tidak ditemukan.")
        return pd.DataFrame()


def classify_prompt_and_extract_entities(current_prompt, previous_prompt=""):
    system_prompt = """
    You are an expert prompt analyzer for a data dashboard. Your goal is to provide a structured and precise search plan.
    IMPORTANT CONTEXT: The current year is 2025.

    **RULES & TASKS:**

    1.  **Classify Type**: Determine if the prompt is "New Topic" or "Follow-Up".

    2.  **Extract Dates**: Convert all mentioned dates to `YYYY-MM-DD` format.

    3.  **Handle Date-Only Follow-Ups**: If the current prompt is clearly just a request for a different date based on the previous topic (e.g., "bagaimana dengan 23 agustus?", "23 agustus saja"), you MUST classify it as **"Follow-Up"**. The `strict_groups` and `fallback_keywords` must be empty `[]` as per the "Follow-Up" rule.

    4.  **Generate Search Keywords (for "New Topic" only):**
        - Identify the CORE ENTITIES (people, organizations, specific topics).
        - **`strict_groups`**: Create a list of lists for high-relevance "AND" searches.
        - **`fallback_keywords`**: Create a flat list for a broader "OR" search.

    5.  **Handle Corrections**: If the current prompt seems to be correcting a typo, extract keywords from the **corrected version only**.

    6.  **Apply Specific Expansions**: To ensure comprehensive results for key topics, apply can apply the following expansions as example for broader cases:
        - If the entity is "Prabowo", you MUST also add "Presiden".
        - If the entity is "Setneg", you MUST also add "Sekertariat Negara".
        - If the entity is "Bahlil", you MUST also add his full name "Bahlil Lahadalia".
        - If the entity is "Menkeu Purbaya", you MUST also add his full tittle "Menteri Keuangan Purbaya".

    7.  **Exclude Non-Searchable Terms**: Do NOT include instructional or conversational words in the keywords. Focus only on the 'who' or 'what'.
    
    8.  **For "Follow-Up" prompts** (that are NOT simple date changes), `strict_groups` and `fallback_keywords` MUST be empty `[]`.

    9.  **Handle Month-Only Queries**: If a user's prompt consists only of a month name (e.g., "agustus", "januari","full september","seluruh apri"), you must interpret this as a date range for the entire month. For example, "agustus" becomes `["2025-08-01", "2025-08-31"]`.
    
    10. **Handle Keyword-Only Non-People Topics**:
    - If the prompt only mentions a non-person topic (e.g., "ekonomi", "keuangan","kementerian") without any date, classify it as **New Topic**.
    - Generate `strict_groups` and `fallback_keywords` based on the core topic(s).
    - Apply optional expansions for relevance (e.g., "ekonomi" can add "keuangan").

    **Output**: Return a single, minified JSON object with keys "type", "dates", "strict_groups", and "fallback_keywords".

    ---
    **EXAMPLES OF CORRECT BEHAVIOR:**

    **Example 1 (Date-Only Follow-Up):**
    Previous Prompt: "data prabowo 20 agustus"
    Current Prompt: "kalau 23 agustus?"
    Result: {{"type":"Follow-Up","dates":["2025-08-23"],"strict_groups":[],"fallback_keywords":[]}}

    **Example 2 (Prabowo -> Presiden):**
    Prompt: "data prabowo 18 agustus"
    Result: {{"type":"New Topic","dates":["2025-08-18"],"strict_groups":[["prabowo"],["prabowo subianto"],["presiden"]],"fallback_keywords":["Prabowo","Prabowo Subianto","Presiden"]}}

    **Example 3 (Bahlil -> Bahlil Lahadalia):**
    Prompt: "data tentang Bahlil"
    Result: {{"type":"New Topic","dates":[],"strict_groups":[["Bahlil"],["Bahlil Lahadalia"]],"fallback_keywords":["Bahlil","Bahlil Lahadalia"]}}

    **Example 4 (Month-Only Follow-Up):**
    Previous Prompt: "data tentang bahlil lahadalia"
    Current Prompt: "agustus/seluruh agustus/full agustus"
    Result: {{"type":"Follow-Up","dates":["2025-08-01","2025-08-31"],"strict_groups":[],"fallback_keywords":[]}}

    **Example 5 (Initial Query with Topic and Month):**
    Prompt: "data menkeu purbaya bulan mei"
    Result: {{"type":"New Topic","dates":["2025-05-01","2025-05-31"],"strict_groups":[["Menteri Keuangan"],["Purbaya"]],"fallback_keywords":["Menkeu Purbaya","Purbaya","Menkeu"]}}

    **Example 6 (Analysis Request as Follow-Up):**
    Previous Prompt: "data surplus keuangan september 1-18"
    Current Prompt: "analisis sentimen dan engagement nya dong"
    Result: {{"type":"Follow-Up","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    **Example 7 (Introducing New Topic Conversationally):**
    Previous Prompt: "data surplus keuangan"
    Current Prompt: "coba cari soal stimulus keuangan"
    Result: {{"type":"New Topic","dates":[],"strict_groups":[["stimulus keuangan"]],"fallback_keywords":["stimulus keuangan"]}}

    **Example 8 (Clarifying Previous Follow-up):**
    Previous Prompt: "analisis sentimennya"
    Current Prompt: "maksudnya dari data surplus keuangan tadi"
    Result: {{"type":"Follow-Up","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    **Example 9 (Initial Query/Follow-Up with Keyword-Only Non-People Topic):**
    Prompt: "Data ekonomi bulan Mei"
    Result: {"type":"New Topic","dates":["2025-05-01","2025-05-31"],"strict_groups":[["Ekonomi"],["Keuangan"]],"fallback_keywords":["Keuangan","Ekonomi"]}
    --- END OF EXAMPLES ---
    **REMEMBER**: Return ONLY the JSON object. No explanations or additional text.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Previous Prompt: \"{previous_prompt}\"\nCurrent Prompt: \"{current_prompt}\""}
            ],
            temperature=0.0, response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "type": result.get("type", "New Topic"),
            "dates": result.get("dates", []),
            "strict_groups": result.get("strict_groups", []),
            "fallback_keywords": result.get("fallback_keywords", [])
        }
    except Exception as e:
        st.error(f"Error classifying prompt: {e}")
        return {"type": "New Topic", "dates": [], "strict_groups": [[current_prompt]], "fallback_keywords": [current_prompt]}


def search_data(dataframe, strict_groups, fallback_keywords, dates):
    if dataframe is None:
        return pd.DataFrame()

    # --- STEP 1: APPLY DATE FILTER FIRST ---
    date_filtered_df = dataframe.copy()
    if dates:
        target_dates = sorted([pd.to_datetime(d).date() for d in dates])

        if len(target_dates) == 1:
            date_filtered_df = date_filtered_df[date_filtered_df['TANGGAL PUBLIKASI'].dt.date == target_dates[0]]
        elif len(target_dates) == 2:
            start_date, end_date = target_dates[0], target_dates[1]
            date_filtered_df = date_filtered_df[
                (date_filtered_df['TANGGAL PUBLIKASI'].dt.date >= start_date) &
                (date_filtered_df['TANGGAL PUBLIKASI'].dt.date <= end_date)
            ]
        else:
            date_filtered_df = date_filtered_df[date_filtered_df['TANGGAL PUBLIKASI'].dt.date.isin(target_dates)]

    if date_filtered_df.empty:
        return pd.DataFrame()

    # --- FIX: If no keywords are provided, return all data for the filtered date range ---
    if not strict_groups and not fallback_keywords:
        return date_filtered_df.sort_values(by='TANGGAL PUBLIKASI')

    # --- STEP 2: NOW, PERFORM KEYWORD SEARCH ONLY ON THE DATE-FILTERED DATA ---
    # TIER 1: Strict Search
    strict_results_df = pd.DataFrame()
    if strict_groups:
        all_matched_dfs = []
        for group in strict_groups:
            if not group: continue
            temp_df = date_filtered_df.copy()
            for keyword in group:
                temp_df = temp_df[temp_df['KONTEN'].str.contains(keyword, case=False, na=False)]
                if temp_df.empty: break
            if not temp_df.empty:
                all_matched_dfs.append(temp_df)

        if all_matched_dfs:
            strict_results_df = pd.concat(all_matched_dfs).drop_duplicates().reset_index(drop=True)

    final_df = strict_results_df

    # TIER 2: Fallback Search (if Tier 1 found nothing)
    if final_df.empty and fallback_keywords:
        search_pattern = '|'.join(fallback_keywords)
        fallback_df = date_filtered_df[date_filtered_df['KONTEN'].str.contains(search_pattern, case=False, na=False)].copy()
        final_df = fallback_df

    if not final_df.empty:
        final_df = final_df.sort_values(by='TANGGAL PUBLIKASI')

    return final_df

# --- NEW: Function to generate structured data for the AI ---
def generate_structured_context_from_data(df):
    """
    Generates a structured dictionary (JSON-like) containing the raw data
    that powers each visualization on the dashboard.
    """
    if df.empty:
        return {"error": "No data available."}

    # Create a safe copy for calculations
    df_copy = df.copy()

    # --- Pre-calculate essential metrics ---
    if 'ENGAGEMENTS' in df_copy.columns and 'VIEWS' in df_copy.columns:
        df_copy['ENGAGEMENT RATE'] = df_copy.apply(
            lambda row: row['ENGAGEMENTS'] / row['VIEWS'] if row['VIEWS'] > 0 else 0, axis=1)
    else:
        df_copy['ENGAGEMENT RATE'] = 0

    if 'ENGAGEMENTS' in df_copy.columns and 'FOLLOWERS' in df_copy.columns:
        df_copy['VIRALITY RATE'] = df_copy.apply(
            lambda row: row['ENGAGEMENTS'] / row['FOLLOWERS'] if row['FOLLOWERS'] > 0 else 0, axis=1)
    else:
        df_copy['VIRALITY RATE'] = 0

    # --- 1. Headline Stats ---
    total_posts = len(df_copy)
    total_views = df_copy['VIEWS'].sum() if 'VIEWS' in df_copy.columns else 0
    avg_engagement_rate = df_copy['ENGAGEMENT RATE'].mean()
    min_date = df_copy['TANGGAL PUBLIKASI'].min().strftime('%Y-%m-%d')
    max_date = df_copy['TANGGAL PUBLIKASI'].max().strftime('%Y-%m-%d')

    # --- 2. Sentiment Distribution ---
    sentiment_counts = df_copy['SENTIMEN'].value_counts().to_dict() if 'SENTIMEN' in df_copy.columns else {}

    # --- 3. Engagement by Category ---
    engagement_by_topic = {}
    if 'TOPIK' in df_copy.columns:
        engagement_by_topic = df_copy.groupby('TOPIK')['ENGAGEMENT RATE'].mean().sort_values(ascending=False).to_dict()

    engagement_by_grup = {}
    if 'GRUP' in df_copy.columns:
        engagement_by_grup = df_copy.groupby('GRUP')['ENGAGEMENT RATE'].mean().sort_values(ascending=False).to_dict()

    # --- 4. Time Series Trends ---
    daily_counts = {}
    if 'TANGGAL PUBLIKASI' in df_copy.columns:
        ts_data = df_copy.set_index('TANGGAL PUBLIKASI').resample('D').size()
        peak_day = ts_data.idxmax()
        peak_count = ts_data.max()
        daily_counts = {
            "peak_day": peak_day.strftime('%Y-%m-%d'),
            "peak_count": int(peak_count),
            "trend_data": {d.strftime('%Y-%m-%d'): v for d, v in ts_data.items()}
        }

    # --- 5. Top Viral Posts ---
    top_viral_posts = []
    if 'VIRALITY RATE' in df_copy.columns and not df_copy.empty:
        top_5 = df_copy.sort_values(by='VIRALITY RATE', ascending=False).head(5)
        top_viral_posts = top_5[['AKUN', 'KONTEN', 'VIRALITY RATE', 'ENGAGEMENTS']].to_dict('records')

    # --- 6. Performance Outliers (Followers vs. Engagement) ---
    performance_outliers = {}
    if not df_copy.empty:
        try:
            top_er_post = df_copy.loc[df_copy['ENGAGEMENT RATE'].idxmax()]
            most_followed_post = df_copy.loc[df_copy['FOLLOWERS'].idxmax()]
            performance_outliers = {
                "highest_engagement_rate_account": {
                    "account": top_er_post.get('AKUN', 'N/A'),
                    "rate": top_er_post.get('ENGAGEMENT RATE', 0)
                },
                "most_followers_account": {
                    "account": most_followed_post.get('AKUN', 'N/A'),
                    "followers": int(most_followed_post.get('FOLLOWERS', 0)),
                    "engagement_rate_at_time": most_followed_post.get('ENGAGEMENT RATE', 0)
                }
            }
        except (KeyError, ValueError):
             performance_outliers = {"error": "Could not determine outliers."}


    # --- Assemble the final JSON structure ---
    structured_context = {
        "overall_summary": {
            "total_posts": total_posts,
            "total_views": int(total_views),
            "average_engagement_rate": avg_engagement_rate,
            "date_range": {"start": min_date, "end": max_date}
        },
        "sentiment_distribution": sentiment_counts,
        "engagement_analysis": {
            "by_topic": engagement_by_topic,
            "by_group": engagement_by_grup
        },
        "daily_trends": daily_counts,
        "top_viral_posts": top_viral_posts,
        "account_performance": performance_outliers
    }
    return structured_context

# Di utils.py, ganti juga dengan fungsi ini
def get_ai_response(prompt, matched_data_df, search_query):
    strict_keywords = {kw for group in search_query.get('strict_groups', []) for kw in group}
    fallback_keywords = set(search_query.get('fallback_keywords', []))
    all_keywords = sorted(list(strict_keywords | fallback_keywords))
    
    if all_keywords:
        topic_context = f"**{', '.join(all_keywords)}**"
        context_awareness_instruction = f"1.  **CONTEXT AWARENESS:** The data you are analyzing has ALREADY been filtered for the topic(s): {topic_context}. ALL data in the JSON is relevant. Frame your answers directly and confidently."
    else:
        topic_context = "all topics for the selected date"
        context_awareness_instruction = "1.  **CONTEXT AWARENESS:** The data has been filtered by date but NOT by a specific topic. Summarize the key findings for the given date range."

    if matched_data_df.empty:
        context = (
            "You are a helpful AI data analyst. Your primary language is Indonesian.\n"
            "**CRITICAL INSTRUCTION:** A search was just performed for the topic "
            f"{topic_context} based on the user's latest prompt ('{prompt}'), but that search returned **ZERO** results. "
            "Your task is to inform the user gracefully that no data could be found. "
            "Acknowledge the topic or date they asked for and state that data for it is unavailable. "
            "Suggest they try another date or topic."
        )
    else:
        structured_data = generate_structured_context_from_data(matched_data_df)
        data_as_json_string = json.dumps(structured_data, indent=2)
        context = (
            "You are a helpful and expert AI data analyst for a social media dashboard. Your primary language is Indonesian, but keep media-specific domain terms (e.g., 'likes', 'comments', 'post', 'views', 'engagement') in English.\n"
            "You will be given a JSON object containing a summary of the data visualized on the user's screen. "
            "Your task is to analyze this JSON to answer the user's question with precision.\n\n"
            "**CRITICAL INSTRUCTIONS:**\n"
            f"{context_awareness_instruction}\n"
            "2.  **FORMATTING:** Use standard Markdown for formatting, especially `**text**` for bolding. Do NOT use HTML tags.\n"
            "3.  **DATA-DRIVEN:** Base your answers *exclusively* on the data in the JSON. Refer to specific numbers and facts, but not necessarily copying all the json as answers.\n\n"
            "Here is the data for the user's current view:\n"
            f"```json\n{data_as_json_string}\n```\n\n"
            "Based *only* on the JSON data above, answer the user's prompt but remember to keep focus on whats importants and interesting, not only reading the data."
        )

    conversation_history = st.session_state.messages.copy()
    conversation_history.insert(0, {"role": "system", "content": context})
    try:
        response_stream = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": m["role"], "content": m["content"]} for m in conversation_history],
            stream=True
        )
        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"Error generating AI response: {e}")
        yield "Maaf, terjadi kesalahan saat memproses permintaan Anda."
        
def get_no_data_suggestion(prompt):
    """Generates a streaming response for when no data is found."""
    response_text = f"Maaf, saya tidak dapat menemukan data apa pun yang terkait dengan '{prompt}'. Silakan coba kata kunci atau topik lain."
    for word in response_text.split():
        yield word + " "
        time.sleep(0.05)