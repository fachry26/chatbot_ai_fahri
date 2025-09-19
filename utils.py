import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime

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

# --- UPDATED FUNCTION WITH TIERED SEARCH LOGIC ---
def classify_prompt_and_extract_entities(current_prompt, previous_prompt=""):
    system_prompt = f"""
    You are an expert prompt analyzer for a data dashboard. Your goal is to provide a structured search plan.
    IMPORTANT CONTEXT: The current year is 2025.

    **RULES & TASKS:**
    1.  **Classify Type**: Classify the prompt as "New Topic" or "Follow-Up".
        - "New Topic": Introduces new entities/concepts not in the previous prompt.
        - "Follow-Up": Continues analysis of the current topic. It can, however, introduce a new date to re-filter the existing data.

    2.  **Extract Dates**: Convert any mentioned dates to strict `YYYY-MM-DD` format. This is critical.
        - "18 agustus" -> "2025-08-18".
        - "kalau 15 agustus?" -> The type is "Follow-Up", but you must still extract the date "2025-08-15".

    3.  **Generate Search Keywords (for "New Topic" only):**
        - **`strict_groups`**: A list of lists. Each inner list contains keywords for a high-relevance "AND" search. These are phrases or concepts.
        - **`fallback_keywords`**: A flat list of all relevant single keywords for a broader "OR" search if the strict search fails.
    
    4.  **For "Follow-Up" prompts**, `strict_groups` and `fallback_keywords` MUST be empty `[]`, unless a new date is the only change.

    **Output**: Return a single, minified JSON object with keys "type", "dates", "strict_groups", and "fallback_keywords".

    **Example 1 (New Topic):**
    Prompt: "data prabowo 18 agustus"
    Result: {{"type":"New Topic","dates":["2025-08-18"],"strict_groups":[["prabowo"],["prabowo subianto"]],"fallback_keywords":["prabowo","prabowo subianto","menhan"]}}

    **Example 2 (Follow-up with Date Change):**
    Previous: "data prabowo"
    Current: "kalau 15 agustus?"
    Result: {{"type":"Follow-Up","dates":["2025-08-15"],"strict_groups":[],"fallback_keywords":[]}}
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

# --- REWRITTEN FUNCTION WITH TIERED SEARCH ---
def search_data(dataframe, strict_groups, fallback_keywords, dates):
    if dataframe is None: return pd.DataFrame()

    # --- TIER 1: Strict Search (AND logic within groups, OR logic between groups) ---
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

    # --- Final Date Filtering ---
    if dates:
        target_dates = [pd.to_datetime(d) for d in dates]
        final_df = final_df[final_df['TANGGAL PUBLIKASI'].dt.date.isin([d.date() for d in target_dates])]

    if not final_df.empty:
        final_df = final_df.sort_values(by='TANGGAL PUBLIKASI')
        
    return final_df

# ... other utility functions like summarize_visual_insights, get_ai_response, etc. are unchanged ...
def summarize_visual_insights(df):
    if df.empty: return "No data available to summarize."
    try:
        total_posts = len(df)
        sentiment_counts = df['SENTIMEN'].value_counts()
        top_topics = df['TOPIK'].value_counts().nlargest(3)
        top_topics_str = "\n".join([f"- {topic} ({count} posts)" for topic, count in top_topics.items()])
        most_viral_post = df.loc[df['ENGAGEMENTS'].idxmax()]
        min_date = pd.to_datetime(df['TANGGAL PUBLIKASI']).dt.date.min().strftime('%d %B %Y')
        max_date = pd.to_datetime(df['TANGGAL PUBLIKASI']).dt.date.max().strftime('%d %B %Y')
        date_range = f"{min_date} to {max_date}" if min_date != max_date else min_date
        summary = f"""
        ### 📊 Dashboard Summary
        - **Date Range:** {date_range}
        - **Total Posts Found:** {total_posts}
        **Public Sentiment:**
        - Positive: {sentiment_counts.get('Positive', 0)}
        - Negative: {sentiment_counts.get('Negative', 0)}
        - Neutral: {sentiment_counts.get('Neutral', 0)}
        **Top Topics:**
        {top_topics_str if top_topics_str else "N/A"}
        **Most Engaging Post:**
        - Engagements: {most_viral_post.get('ENGAGEMENTS', 0):,}
        - Content: "{most_viral_post.get('KONTEN', 'N/A')[:100]}..."
        """
        return summary.strip()
    except Exception: return "An error occurred while summarizing data."

def get_ai_response(prompt, matched_data_df):
    if matched_data_df.empty:
        context = "No relevant data found. Inform the user gracefully."
    else:
        visual_summary = summarize_visual_insights(matched_data_df)
        context = (
            "You are an AI assistant in a data dashboard. Interpret this summary of visualized data to answer the user's question.\n\n"
            f"Here is the summary of the data they are looking at:\n{visual_summary}\n\n"
            "Based *only* on the summary above, answer the user's prompt."
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
        yield "Sorry, an error occurred."

def get_no_data_suggestion(prompt):
    """Generates a streaming response for when no data is found."""
    response_text = f"Maaf, saya tidak dapat menemukan data apa pun yang terkait dengan '{prompt}'. Silakan coba kata kunci atau topik lain."
    for word in response_text.split():
        yield word + " "
        time.sleep(0.05) # Jeda singkat untuk simulasi mengetik