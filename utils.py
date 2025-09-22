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
def load_data(file_path="data.xlsx"):
    try:
        df = pd.read_excel(file_path)
        df['TANGGAL PUBLIKASI'] = pd.to_datetime(df['TANGGAL PUBLIKASI'])
        return df
    except FileNotFoundError:
        st.error(f"Error: The file {file_path} was not found. Please create it.")
        return None

# In utils.py

# ... (other functions remain the same) ...

# In utils.py

# ... (other functions remain the same) ...

# In utils.py

# ... (other functions remain the same) ...

def classify_prompt_and_extract_entities(current_prompt, previous_prompt=""):
    system_prompt = f"""
    You are an expert prompt analyzer for a data dashboard. Your goal is to provide a structured and precise search plan.
    IMPORTANT CONTEXT: The current year is 2025.

    **RULES & TASKS:**

    1.  **Classify Type**: Determine if the prompt is "New Topic" or "Follow-Up".

    2.  **Extract Dates**: Convert all mentioned dates to `YYYY-MM-DD` format.

    3.  **Generate Search Keywords (for "New Topic" only):**
        - Identify the CORE ENTITIES (people, organizations, specific topics).
        - **`strict_groups`**: Create a list of lists for high-relevance "AND" searches.
        - **`fallback_keywords`**: Create a flat list for a broader "OR" search.

    4.  **Handle Corrections**: If the current prompt seems to be correcting a typo in the previous prompt (e.g., using words like 'maksud saya', 'maaf', or just providing a corrected name), extract the keywords from the **corrected version only**. Do not combine the typo with the correction.

    5.  **Apply Specific Expansions**: To ensure comprehensive results for key topics, apply ONLY the following expansions:
        - If the entity is "Prabowo", you MUST also add "Presiden".
        - If the entity is "Setneg", you MUST also add "Sekertariat Negara".
        - If the entity is "Bahlil", you MUST also add his full name "Bahlil Lahadalia".

    6.  **Exclude Non-Searchable Terms**: Do NOT include instructional, conversational (e.g., 'maaf', 'maksud saya'), or analytical words in the keywords. Focus only on the 'who' or 'what'.
    
    7.  **For "Follow-Up" prompts**, `strict_groups` and `fallback_keywords` MUST be empty `[]`.

    **Output**: Return a single, minified JSON object with keys "type", "dates", "strict_groups", and "fallback_keywords".

    ---
    **EXAMPLES OF CORRECT BEHAVIOR:**

    **Example 1 (Correction):**
    Previous Prompt: "data bahli"
    Current Prompt: "maksud saya bahlil"
    Result: {{"type":"New Topic","dates":[],"strict_groups":[["bahlil"],["bahlil lahadalia"]],"fallback_keywords":["Bahlil","Bahlil Lahadalia"]}}

    **Example 2 (Prabowo -> Presiden):**
    Prompt: "data prabowo 18 agustus"
    Result: {{"type":"New Topic","dates":["2025-08-18"],"strict_groups":[["prabowo"],["prabowo subianto"],["presiden"]],"fallback_keywords":["Prabowo","Prabowo Subianto","Presiden"]}}

    **Example 3 (Bahlil -> Bahlil Lahadalia):**
    Prompt: "data tentang Bahlil"
    Result: {{"type":"New Topic","dates":[],"strict_groups":[["Bahlil"],["Bahlil Lahadalia"]],"fallback_keywords":["Bahlil","Bahlil Lahadalia"]}}
    ---
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

# ... (the rest of the functions in utils.py remain the same) ...

def search_data(dataframe, strict_groups, fallback_keywords, dates):
    if dataframe is None: return pd.DataFrame()

    # --- TIER 1: Strict Search ---
    strict_results_df = pd.DataFrame()
    if strict_groups:
        all_matched_dfs = []
        for group in strict_groups:
            if not group: continue
            temp_df = dataframe.copy()
            for keyword in group:
                temp_df = temp_df[temp_df['KONTEN'].str.contains(keyword, case=False, na=False)]
                if temp_df.empty: break
            if not temp_df.empty:
                all_matched_dfs.append(temp_df)
        
        if all_matched_dfs:
            strict_results_df = pd.concat(all_matched_dfs).drop_duplicates().reset_index(drop=True)

    final_df = strict_results_df

    # --- TIER 2: Fallback Search (if Tier 1 found nothing) ---
    if final_df.empty and fallback_keywords:
        search_pattern = '|'.join(fallback_keywords)
        fallback_df = dataframe[dataframe['KONTEN'].str.contains(search_pattern, case=False, na=False)].copy()
        final_df = fallback_df

    # --- Final Date Filtering (NOW HANDLES RANGES) ---
    if dates and not final_df.empty:
        target_dates = sorted([pd.to_datetime(d).date() for d in dates])
        
        if len(target_dates) == 1:
            final_df = final_df[final_df['TANGGAL PUBLIKASI'].dt.date == target_dates[0]]
        elif len(target_dates) == 2:
            start_date, end_date = target_dates[0], target_dates[1]
            final_df = final_df[(final_df['TANGGAL PUBLIKASI'].dt.date >= start_date) & (final_df['TANGGAL PUBLIKASI'].dt.date <= end_date)]
        else:
            final_df = final_df[final_df['TANGGAL PUBLIKASI'].dt.date.isin(target_dates)]

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

# --- UPDATED: The AI response function now uses the structured context ---
# In utils.py

# ... (all other functions like configure_openai, load_data, classify_prompt_and_extract_entities, search_data, generate_structured_context_from_data remain the same) ...

# --- UPDATED: The AI response function now uses the structured context AND the search query ---
def get_ai_response(prompt, matched_data_df, search_query):
    if matched_data_df.empty:
        context = "No relevant data found. Inform the user gracefully and suggest another search."
    else:
        # Generate the new structured data context
        structured_data = generate_structured_context_from_data(matched_data_df)
        data_as_json_string = json.dumps(structured_data, indent=2)

        # --- NEW: Extract keywords to give the AI context about the search topic ---
        strict_keywords = {kw for group in search_query.get('strict_groups', []) for kw in group}
        fallback_keywords = set(search_query.get('fallback_keywords', []))
        all_keywords = sorted(list(strict_keywords | fallback_keywords))
        topic_context = f"The user is asking about '{', '.join(all_keywords)}'."

        context = (
            "You are a helpful and expert AI data analyst for a social media dashboard. Your primary language is Indonesian.But domain knowledge for MEDIA e.g. 'likes', 'comments', 'post', 'views', 'enggagement' remains English.\n"
            "You will be given a JSON object that contains all the data currently being visualized on the user's screen. "
            "Your task is to analyze this JSON data to answer the user's question with precision and clarity.\n\n"
            "**CRITICAL INSTRUCTIONS:**\n"
            f"1.  **CONTEXT AWARENESS:** The data you are analyzing has ALREADY been filtered for the topic(s): <b>{', '.join(all_keywords)}</b>. ALL data in the JSON is relevant to this topic. Frame your answers directly and confidently without stating that the data is limited.\n"
            "2.  **FORMATTING:** For emphasis or bolding, you MUST use HTML `<b>` tags, not Markdown (`**`). The user interface can only render HTML tags.\n"
            "3.  **DATA-DRIVEN:** Base your answers *exclusively* on the data in the JSON. Refer to specific numbers, percentages, topics, or accounts to support your answer.\n"
            "4.  **LANGUAGE:** All your responses must be in clear and professional Indonesian. But domain knowledge for MEDIA e.g. 'likes', 'comments', 'post', 'views', 'enggagement' remains English.\n\n"
            "Here is the data for the user's current view:\n"
            f"```json\n{data_as_json_string}\n```\n\n"
            "Based *only* on the JSON data above, answer the user's prompt."
        )

    # The rest of the function remains the same
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