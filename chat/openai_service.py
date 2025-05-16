import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAIAgent:
    def process_query(self, message_text, conversation_history, model_name=None):
        messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
        messages.append({"role": "user", "content": message_text})
        # Выбор модели: если явно указано, используем её, иначе gpt-4o
        model = model_name or "gpt-4o"
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return {"message": response.choices[0].message.content}

openai_ai = OpenAIAgent() 