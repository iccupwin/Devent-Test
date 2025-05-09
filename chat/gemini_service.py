import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiAgent:
    def process_query(self, message_text, conversation_history):
        url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        
        # Format conversation history with proper roles
        contents = []
        for message in conversation_history:
            role = "user" if message.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": message["content"]}]
            })
        
        # Add the current message
        contents.append({
            "role": "user",
            "parts": [{"text": message_text}]
        })
        
        data = {"contents": contents}
        params = {"key": GEMINI_API_KEY}
        
        resp = requests.post(url, headers=headers, params=params, json=data)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # Return detailed error message to user
            return {"message": f"Ошибка Gemini API: {resp.status_code} {resp.text}"}
            
        result = resp.json()
        return {"message": result["candidates"][0]["content"]["parts"][0]["text"]}

gemini_ai = GeminiAgent() 