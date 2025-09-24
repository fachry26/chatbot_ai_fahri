# history_service.py

import os
import json
import uuid
import pandas as pd
from datetime import datetime

# The directory where chat history files will be stored
HISTORY_DIR = "chat_history"

def setup_history():
    """Ensures the history directory exists."""
    os.makedirs(HISTORY_DIR, exist_ok=True)

def save_chat_session(session_state):
    """
    Saves the current chat session state to a JSON file.
    The session state should be a dictionary containing messages, matched_data, etc.
    """
    setup_history()
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    messages = session_state.get("messages", [])
    matched_data = session_state.get("matched_data", pd.DataFrame())
    last_search = session_state.get("last_search", {})
    
    # Generate a summary from the first user message for the history list
    summary = "Chat Session"
    for msg in messages:
        if msg.get("role") == "user":
            summary = msg.get("content", "Chat Session")[:40] + "..."
            break

    # Convert the pandas DataFrame to a JSON string to store it
    data_json = matched_data.to_json(orient='split', date_format='iso') if not matched_data.empty else None

    session_data = {
        "id": session_id,
        "summary": summary,
        "timestamp": timestamp,
        "messages": messages,
        "data_json": data_json,
        "last_search": last_search
    }
    
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=4)

def load_chat_sessions():
    """
    Loads metadata for all chat sessions from the history directory,
    sorted with the newest chats first.
    """
    setup_history()
    sessions = []
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # For the history list, we only need summary data
                    sessions.append({
                        "id": data.get("id"),
                        "summary": data.get("summary", "Untitled Chat"),
                        "timestamp": data.get("timestamp"),
                        "message_count": len(data.get("messages", []))
                    })
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted or invalid files
                continue
    
    # Sort sessions by timestamp in descending order (newest first)
    sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return sessions

def load_specific_session(session_id):
    """Loads the full state of a single chat session from its file."""
    setup_history()
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    # Reconstruct the DataFrame from its JSON representation
    if session_data.get("data_json"):
        matched_data = pd.read_json(session_data["data_json"], orient='split')
    else:
        matched_data = pd.DataFrame()
        
    return {
        "messages": session_data.get("messages", []),
        "matched_data": matched_data,
        "last_search": session_data.get("last_search", {}),
        "search_performed": not matched_data.empty
    }

def delete_chat_session(session_id):
    """Deletes a chat session file."""
    setup_history()
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except OSError:
            return False
    return False