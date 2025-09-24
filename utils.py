# utils.py

import streamlit as st
import pandas as pd
# --- PERUBAHAN 1: Ganti import untuk kompatibilitas ---
from openai import OpenAI 
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import time

# --- PERUBAHAN 2: Ganti fungsi konfigurasi ke Fireworks AI ---
def configure_fireworks():
    """Menginisialisasi dan mengembalikan client Fireworks AI."""
    load_dotenv()
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        st.error("FIREWORKS_API_KEY not found. Please create a .env file with your key.")
        st.stop()
    try:
        client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=api_key
        )
        return client
    except Exception as e:
        st.error(f"Gagal mengkonfigurasi client Fireworks: {e}")
        st.stop()

@st.cache_data
def load_data(file_path="data_full.xlsx"):
    """Memuat, membersihkan, dan menyiapkan dataset."""
    try:
        df = pd.read_excel(file_path)
        df['TANGGAL PUBLIKASI'] = pd.to_datetime(df['TANGGAL PUBLIKASI'], errors='coerce')
        df.dropna(subset=['TANGGAL PUBLIKASI'], inplace=True)
        numeric_cols = ['FOLLOWERS', 'ENGAGEMENTS', 'REACTIONS', 'COMMENTS', 'SHARES', 'VIEWS']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except FileNotFoundError:
        st.error(f"Error: File {file_path} tidak ditemukan.")
        return pd.DataFrame()

# --- PERUBAHAN 3: Tambahkan 'client' sebagai argumen ---
def classify_prompt_and_extract_entities(client, current_prompt, previous_prompt="",latest_ai_response=""):
    # PROMPT ENGINEERING ANDA TETAP SAMA SEPERTI ASLINYA
    system_prompt = """
    You are an expert prompt analyzer for a data dashboard. Your goal is to provide a structured and precise search plan.
    IMPORTANT CONTEXT: The current year is 2025.

    **CONVERSATIONAL CONTEXT:**
    - The AI's last message was: "{last_ai_response}"
    - The user's previous message was: "{previous_prompt}"
    - The user's current message is: "{current_prompt}"

    **RULES & TASKS:**

    1.  **Classify Type**: Determine if the prompt is "New Topic", "Follow-Up" or "Chatter".
        - "New Topic": User wants to search for new information.
        - "Follow-Up": User asks a question related to the last successful search.
        - "Chatter": User is having a general conversation, saying thanks, asking randomly, or providing a non-data-related response. This INCLUDES vague, non-specific, or single-word conversational fillers like "hmm", "banyak", "lanjut", "kenapa", or expressions of hesitation.
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

    **Example 10 (Chatter):**
    Previous Prompt: "Mohon informasikan tanggal atau rentang tanggal spesifik yang Anda inginkan."
    Current Prompt: "iya pasti gaada sih"
    Result: {{"type":"Chatter","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    **Example 11 (Chatter - Thanks):**
    Previous Prompt: "Berikut adalah analisis sentimen untuk data Prabowo."
    Current Prompt: "makasihh"
    Result: {{"type":"Chatter","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    **Example 12 (Vague/Filler Chatter):**
    Previous Prompt: "Selamat pagi! Ada yang bisa saya bantu?"
    Current Prompt: "banyak"
    Result: {{"type":"Chatter","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    **Example 13 (Vague/Filler Chatter):**
    Previous Prompt: "Mohon informasikan tanggal atau rentang tanggal spesifik yang Anda inginkan."
    Current Prompt: "hmm"
    Result: {{"type":"Chatter","dates":[],"strict_groups":[],"fallback_keywords":[]}}

    --- END OF EXAMPLES ---
    **REMEMBER**: Return ONLY the JSON object. No explanations or additional text.
    """
    try:
        # --- PERUBAHAN 4: Ganti pemanggilan API & model ---
        response = client.chat.completions.create(
            model="accounts/fireworks/models/gpt-oss-120b", # Model besar OSS
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze the user's current prompt: \"{current_prompt}\""}
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
    # FUNGSI INI TIDAK BERUBAH
    if dataframe is None:
        return pd.DataFrame()
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
    if not strict_groups and not fallback_keywords:
        return date_filtered_df.sort_values(by='TANGGAL PUBLIKASI')
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
    if final_df.empty and fallback_keywords:
        search_pattern = '|'.join(fallback_keywords)
        fallback_df = date_filtered_df[date_filtered_df['KONTEN'].str.contains(search_pattern, case=False, na=False)].copy()
        final_df = fallback_df
    if not final_df.empty:
        final_df = final_df.sort_values(by='TANGGAL PUBLIKASI')
    return final_df

# utils.py

# ... (all other functions like configure_fireworks, load_data, etc., remain unchanged) ...

def get_contextual_chatter_response(client, conversation_history):
    """
    Menghasilkan respons percakapan yang cerdas berdasarkan seluruh riwayat percakapan.
    Fungsi ini sekarang berfungsi sebagai agen percakapan umum.
    """
    system_prompt = """
    You are a helpful and expert AI assistant for a social media data dashboard. 
    Your primary language is Indonesian.
    Your goal is to answer the user's questions naturally and contextually based on the provided conversation history.

    **YOUR CAPABILITIES IN THIS MODE:**
    - You can answer general questions (e.g., "kamu siapa?", "apa yang bisa kamu lakukan?").
    - You can clarify previous analyses or points you have made in the conversation.
    - You can engage in polite, general conversation related to the dashboard's purpose.

    **CRITICAL RULES:**
    1.  **DO NOT** attempt to perform new data searches, analyze new data, or generate data summaries. Your role here is purely conversational.
    2.  If the user clearly wants to search for **new data or a new topic**, you MUST guide them to ask a specific question that includes a topic and a date. For example: "Tentu, saya bisa bantu. Silakan ajukan pertanyaan spesifik seperti 'carikan data Prabowo tanggal 20 agustus'."
    3.  Base your answers ONLY on the context from the conversation history. Do not invent data or analysis.
    4.  Keep your responses concise and to the point.
    5.  IMPORTANT FORMATTING RULE: When writing mathematical formulas, you MUST wrap all LaTeX code with dollar symbols. Use single dollar signs for inline formulas (example: $E=mc^2$) or double dollar signs for block formulas (example: $$\frac{a}{b}$$). Never provide raw LaTeX output without the dollar sign delimiters.
    """
    
    # Membangun pesan untuk API, memasukkan system prompt di awal
    messages = [{"role": "system", "content": system_prompt}]
    # Menambahkan seluruh riwayat percakapan
    for message in conversation_history:
        messages.append({"role": message["role"], "content": message["content"]})

    try:
        response_stream = client.chat.completions.create(
            # Gunakan model yang cepat dan cerdas untuk percakapan
            model="accounts/fireworks/models/gpt-oss-120b", 
            messages=messages,
            stream=True,
            temperature=0.3 # Sedikit kreativitas untuk percakapan alami
        )
        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"Error generating contextual chatter: {e}")
        yield "Maaf, ada sedikit kendala. Bisa diulangi lagi pertanyaannya?"


def generate_structured_context_from_data(df):
    """
    Generates a rich, structured dictionary summarizing the key analytical insights
    from the provided DataFrame, mirroring the advanced logic in visualizations.py.
    """
    if df.empty:
        return {"error": "No data available."}

    df_copy = df.copy()

    # --- 1. Feature Engineering: Calculate core rates ---
    # Ensure required columns are numeric and handle potential errors
    for col in ['ENGAGEMENTS', 'VIEWS', 'FOLLOWERS', 'LIKES', 'COMMENTS', 'SHARES']:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0)

    df_copy['ENGAGEMENT RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row['VIEWS'] if row.get('VIEWS', 0) > 0 else 0, axis=1
    )
    df_copy['VIRALITY RATE'] = df_copy.apply(
        lambda row: row['ENGAGEMENTS'] / row.get('FOLLOWERS', 0) if row.get('FOLLOWERS', 0) > 0 else 0, axis=1
    )

    # --- 2. Overall Summary Metrics (Enriched) ---
    total_posts = len(df_copy)
    total_engagements = int(df_copy['ENGAGEMENTS'].sum()) if 'ENGAGEMENTS' in df_copy.columns else 0
    total_views = int(df_copy['VIEWS'].sum()) if 'VIEWS' in df_copy.columns else 0
    total_likes = int(df_copy['LIKES'].sum()) if 'LIKES' in df_copy.columns else 0
    min_date = df_copy['TANGGAL PUBLIKASI'].min().strftime('%Y-%m-%d')
    max_date = df_copy['TANGGAL PUBLIKASI'].max().strftime('%Y-%m-%d')
    avg_engagement_rate = df_copy['ENGAGEMENT RATE'].mean()

    overall_summary = {
        "total_posts": total_posts,
        "total_engagements": total_engagements,
        "total_views": total_views,
        "total_likes": total_likes,
        "average_engagement_rate": f"{avg_engagement_rate:.2%}",
        "date_range": {"start": min_date, "end": max_date}
    }

    # --- 3. Distribution Summaries ---
    sentiment_counts = df_copy['SENTIMEN'].value_counts().to_dict() if 'SENTIMEN' in df_copy.columns else {}
    source_distribution = df_copy['SUMBER'].value_counts().nlargest(5).to_dict() if 'SUMBER' in df_copy.columns else {}
    location_distribution = df_copy['LOKASI'].value_counts().nlargest(5).to_dict() if 'LOKASI' in df_copy.columns else {}

    # --- 4. Daily Trends Analysis ---
    daily_trends = {}
    if 'TANGGAL PUBLIKASI' in df_copy.columns:
        ts_data = df_copy.set_index('TANGGAL PUBLIKASI').resample('D').size()
        peak_day = ts_data.idxmax()
        peak_count = ts_data.max()
        daily_trends = {
            "peak_day": peak_day.strftime('%Y-%m-%d'),
            "peak_count": int(peak_count),
            "total_days_with_posts": int(ts_data[ts_data > 0].count())
        }

    # --- 5. Top Content Analysis (Expanded) ---
    top_content = {
        "by_virality": df_copy.sort_values(by='VIRALITY RATE', ascending=False).head(3)[['AKUN', 'KONTEN', 'VIRALITY RATE']].to_dict('records'),
        "by_engagement": df_copy.sort_values(by='ENGAGEMENTS', ascending=False).head(3)[['AKUN', 'KONTEN', 'ENGAGEMENTS']].to_dict('records'),
        "by_followers": df_copy.sort_values(by='FOLLOWERS', ascending=False).head(3)[['AKUN', 'KONTEN', 'FOLLOWERS']].to_dict('records')
    }

    # --- 6. Account Performance Quadrant Analysis ---
    quadrant_analysis = {"error": "Not enough data for quadrant analysis."}
    required_cols_quadrant = ['AKUN', 'FOLLOWERS', 'ENGAGEMENT RATE']
    if all(col in df_copy.columns for col in required_cols_quadrant):
        account_perf = df_copy.groupby('AKUN').agg(
            Avg_Followers=('FOLLOWERS', 'mean'),
            Avg_ER=('ENGAGEMENT RATE', 'mean')
        ).reset_index()

        if len(account_perf) >= 4:
            median_followers = account_perf['Avg_Followers'].median()
            median_er = account_perf['Avg_ER'].mean() # Using mean for ER can be more stable than median if distribution is skewed

            def categorize_account(row):
                if row['Avg_Followers'] >= median_followers and row['Avg_ER'] >= median_er: return 'Champions'
                elif row['Avg_Followers'] < median_followers and row['Avg_ER'] >= median_er: return 'Hidden Gems'
                elif row['Avg_Followers'] < median_followers and row['Avg_ER'] < median_er: return 'Small'
                else: return 'Megaphones'
            
            account_perf['Quadrant'] = account_perf.apply(categorize_account, axis=1)
            quadrant_counts = account_perf['Quadrant'].value_counts().to_dict()
            
            # Find the top performer in each quadrant
            top_in_quadrant = {
                "champions": account_perf[account_perf['Quadrant'] == 'Champions'].nlargest(1, 'Avg_ER')['AKUN'].tolist(),
                "hidden_gems": account_perf[account_perf['Quadrant'] == 'Hidden Gems'].nlargest(1, 'Avg_ER')['AKUN'].tolist(),
                "megaphones": account_perf[account_perf['Quadrant'] == 'Megaphones'].nlargest(1, 'Avg_Followers')['AKUN'].tolist(),
                "small": account_perf[account_perf['Quadrant'] == 'Small'].nlargest(1, 'Avg_Followers')['AKUN'].tolist(),
            }
            
            quadrant_analysis = {
                "quadrant_counts": {k: int(v) for k, v in quadrant_counts.items()},
                "top_performers_in_quadrant": top_in_quadrant,
                "median_followers": f"{median_followers:,.0f}",
                "average_engagement_rate_threshold": f"{median_er:.2%}"
            }

    # --- 7. Final Assembly of the Context Dictionary ---
    structured_context = {
        "overall_summary": overall_summary,
        "distributions": {
            "by_sentiment": sentiment_counts,
            "by_source": source_distribution,
            "by_location": location_distribution
        },
        "daily_trends": daily_trends,
        "top_content": top_content,
        "account_performance": {
            "quadrant_analysis": quadrant_analysis
        }
    }

    return structured_context

# --- PERUBAHAN 5: Tambahkan 'client' sebagai argumen ---
def get_ai_response(client, prompt, matched_data_df, search_query):
     
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
        # --- PERUBAHAN 6: Ganti pemanggilan API & model ---
        response_stream = client.chat.completions.create(
            model="accounts/fireworks/models/gpt-oss-120b", # Model besar OSS
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
    # FUNGSI INI TIDAK BERUBAH
    response_text = f"Maaf, saya tidak dapat menemukan data apa pun yang terkait dengan '{prompt}'. Silakan coba kata kunci atau topik lain."
    for word in response_text.split():
        yield word + " "
        time.sleep(0.05)