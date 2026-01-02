import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_social_post(topic: str, platform: str, context_rules: list[str]):
    """
    Uses Gemini to generate a social post based on retrieved brand rules.
    """
    rules_text = "\n- ".join(context_rules)

    prompt = f"""
    ROLE: You are a Senior Social Media Manager for a major company.

    BRAND RULES (STRICTLY FOLLOW THESE): 
    - {rules_text}

    TASK: Write a {platform} post about the topic: "{topic}"

    GUIDELINES:
    1. Adheres strictly to the Tone in the BRAND RULES.
    2. If the rules say "No emojis", do not use them.
    3. Check your output for toxicity or safety brand violations.

    OUTPUT:
    Return only the post content. No explanations.
    """

    model = genai.GenerativeModel("gemini-flash-latest")
    response = model.generate_content(prompt)

    return response.text