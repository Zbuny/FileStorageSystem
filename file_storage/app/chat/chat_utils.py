import google.generativeai as genai
from flask import current_app

def ask_openai(prompt, file_text):
    try:
        genai.configure(api_key=current_app.config.get("GEMINI_API_KEY"))

        model = genai.GenerativeModel("models/gemini-2.0-flash")

        context = file_text[:3000] if file_text else "Документ пуст или нераспознан."

        response = model.generate_content(
            f"""You are a smart assistant helping the user understand a document.
Here is the document content:
\"\"\"{context}\"\"\"

Answer the question: {prompt}
""",
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 512,
            }
        )

        return response.text

    except Exception as e:
        return f"⚠️ Gemini API Error: {e}"
