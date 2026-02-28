from flask import Flask, render_template, request, send_file
from gtts import gTTS
from gtts.tts import gTTSError
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

import os
import requests
import time
import math
import re
from dotenv import load_dotenv

# ---------------- LOAD .ENV ---------------- #
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    print("[startup] HF_API_KEY not found in .env! API calls will use fallback story mode.")

# ---------------- FLASK SETUP ---------------- #
app = Flask(__name__, static_folder="static")

# ---------------- HUGGING FACE ROUTER API ---------------- #
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_CANDIDATES = [
    "moonshotai/Kimi-K2-Instruct-0905:fastest",
    "Qwen/Qwen3.5-35B-A3B",
    "meta-llama/Llama-3.1-8B-Instruct",
]

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

# ---------------- STORY GENERATION ---------------- #
def generate_story_hf(prompt, retries=3):
    if not HF_API_KEY:
        return "API Error: Missing HF_API_KEY."

    for model in MODEL_CANDIDATES:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a creative storyteller. Write complete, readable stories with clear structure."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            "temperature": 0.7,
            "max_tokens": 800,
        }

        for attempt in range(retries):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
                print(f"[HF] Model: {model} | Status: {response.status_code}")
                safe_snippet = response.text[:500].encode("ascii", "backslashreplace").decode("ascii")
                print(f"[HF] Response (truncated): {safe_snippet}")

                if response.status_code == 401:
                    return "API Error: Token invalid or expired."
                if response.status_code == 403:
                    return "API Error: Token lacks required inference permissions."
                if response.status_code in (404, 422):
                    break
                if response.status_code != 200:
                    if attempt < retries - 1:
                        time.sleep(1.5)
                        continue
                    break

                result = response.json()
                choices = result.get("choices", [])
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", "").strip()
                    if content:
                        return content
                return "Unexpected response from Hugging Face API."

            except Exception as e:
                print(f"[HF] Model {model} attempt {attempt+1} error: {e}")
                if attempt < retries - 1:
                    time.sleep(1.5)
                else:
                    break

    return "Error: Unable to get story from Hugging Face after trying available models."


def generate_story_fallback(genre, characters, setting, tone, length):
    target_words = max(120, min(int(length), 900))
    opening = (
        f"In {setting}, {characters} began a {tone.lower()} {genre.lower()} journey that started with a small decision "
        "and slowly grew into something bigger than anyone expected. "
    )
    middle = (
        "At first, every step felt uncertain, and each challenge seemed designed to make them give up. "
        "But with patience, teamwork, and courage, they solved one problem at a time and discovered strengths they did not know they had. "
        "When mistakes happened, they learned from them instead of hiding from them, and that made them stronger. "
    )
    ending = (
        "In the end, they chose kindness over fear and responsibility over comfort. "
        "Their final choice helped not only themselves but also the people around them. "
        "The story shows that growth comes from brave decisions, and even difficult paths can lead to hopeful endings."
    )

    text = f"{opening}{middle}{ending}"
    while len(text.split()) < target_words:
        text += " " + middle

    words = text.split()[:target_words]
    return " ".join(words)


def generate_story_fallback_malayalam(genre, characters, setting, tone, length):
    target_words = max(120, min(int(length), 900))
    opening = (
        f"{setting} എന്ന ലോകത്ത് {characters} ചേർന്ന് ഒരു {tone} ഭാവമുള്ള {genre} യാത്ര തുടങ്ങി. "
        "ചെറിയൊരു തീരുമാനം അവരുടെ ജീവിതത്തെ വലിയ വഴിത്തിരിവിലേക്ക് നയിച്ചു. "
    )
    middle = (
        "ആരംഭത്തിൽ എല്ലാം ബുദ്ധിമുട്ടായിരുന്നു. ഓരോ വെല്ലുവിളിയും പിൻമാറാൻ പ്രേരിപ്പിച്ചു. "
        "എന്നാൽ ധൈര്യവും ക്ഷമയും കൂട്ടായ്മയും കൊണ്ട് അവർ ഓരോ പ്രശ്നവും മറികടന്നു. "
        "പിഴവുകളിൽ നിന്ന് അവർ പഠിച്ചു; അതാണ് അവരെ കൂടുതൽ ശക്തരാക്കിയത്. "
    )
    ending = (
        "അവസാനത്തിൽ അവർ ഭയത്തേക്കാൾ കരുണയെയും സ്വാർത്ഥതയ്ക്കുപകരം ഉത്തരവാദിത്തത്തെയും തിരഞ്ഞെടുത്തു. "
        "അവരുടെ തീരുമാനം അവരുടെ ജീവിതം മാത്രമല്ല, ചുറ്റുമുള്ളവരുടെ ജീവിതവും മാറ്റിമറിച്ചു. "
        "ശരിയായ തീരുമാനം എടുക്കാൻ ധൈര്യം കാണിച്ചാൽ നല്ല അവസാനങ്ങൾ സാധ്യമാണെന്നതാണ് ഈ കഥയുടെ പാഠം."
    )

    text = f"{opening}{middle}{ending}"
    while len(text.split()) < target_words:
        text += " " + middle

    words = text.split()[:target_words]
    return " ".join(words)


def estimate_reading_time_minutes(story_text, words_per_minute=190):
    words = len(story_text.split())
    return max(1, math.ceil(words / words_per_minute)), words


def clean_repeated_sentences(story_text):
    if not story_text or not isinstance(story_text, str):
        return story_text

    raw_sentences = re.split(r"(?<=[.!?])\s+", story_text.strip())
    cleaned = []
    seen = set()

    for sentence in raw_sentences:
        s = sentence.strip()
        if not s:
            continue

        # Normalize for duplicate detection.
        normalized = re.sub(r"\W+", " ", s.lower()).strip()
        if not normalized:
            continue

        # Exact duplicate sentence.
        if normalized in seen:
            continue

        # Near-duplicate of immediately previous sentence.
        if cleaned:
            prev_norm = re.sub(r"\W+", " ", cleaned[-1].lower()).strip()
            if normalized == prev_norm:
                continue
            if normalized in prev_norm or prev_norm in normalized:
                continue

        cleaned.append(s)
        seen.add(normalized)

    return " ".join(cleaned) if cleaned else story_text

# ---------------- AUDIO GENERATION ---------------- #
def generate_audio(story_text, lang="en"):
    if not isinstance(story_text, str):
        return False, "Audio skipped: story text is invalid."

    audio_folder = os.path.join(app.static_folder, "audio")
    os.makedirs(audio_folder, exist_ok=True)
    audio_path = os.path.join(audio_folder, "story.mp3")
    try:
        tts = gTTS(text=story_text, lang=lang)
        tts.save(audio_path)
        return True, None
    except gTTSError:
        return False, "Audio unavailable: could not connect to Google TTS."
    except Exception as e:
        return False, f"Audio unavailable: {str(e)}"

# ---------------- PDF GENERATION ---------------- #
def generate_pdf(story_text, title="KathaAI Story"):
    pdf_path = "story.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.8 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "StoryTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        spaceAfter=16,
    )
    body_style = ParagraphStyle(
        "StoryBody",
        parent=styles["Normal"],
        fontSize=12,
        leading=19,
        spaceAfter=10,
    )

    paragraphs = [p.strip() for p in story_text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [story_text.strip()]

    elements = [Paragraph(title, title_style)]
    for para in paragraphs:
        elements.append(Paragraph(para.replace("\n", "<br/>"), body_style))

    doc.build(elements)

# ---------------- ROUTES ---------------- #
@app.route('/')
def home():
    return render_template("landing.html")


@app.route('/create')
def create_page():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate():
    genre = request.form.get('genre', 'Fiction')
    characters = request.form.get('characters', 'A hero')
    setting = request.form.get('setting', 'A magical land')
    tone = request.form.get('tone', 'Adventurous')
    language = request.form.get('language', 'English')
    length = request.form.get('length', '500').strip()
    if not length.isdigit():
        length = "500"
    if language not in ("English", "Malayalam"):
        language = "English"

    prompt = f"""
Write a {length} word {genre} story in {language}.
Characters: {characters}
Setting: {setting}
Tone: {tone}
Make it engaging and creative.
"""

    story = generate_story_hf(prompt)
    warning = None

    if story.startswith("API Error") or story.startswith("Unexpected") or story.startswith("Error"):
        warning = "Online AI service is unavailable right now. Showing offline story mode."
        if language == "Malayalam":
            story = generate_story_fallback_malayalam(genre, characters, setting, tone, length)
        else:
            story = generate_story_fallback(genre, characters, setting, tone, length)

    story = clean_repeated_sentences(story)
    read_minutes, word_count = estimate_reading_time_minutes(story)
    audio_lang = "ml" if language == "Malayalam" else "en"
    audio_ok, audio_message = generate_audio(story, lang=audio_lang)
    generate_pdf(story, title=f"{genre} Story")

    audio_exists = os.path.exists(os.path.join(app.static_folder, "audio", "story.mp3"))
    if not audio_ok:
        audio_exists = False

    if audio_message:
        if warning:
            warning = f"{warning} {audio_message}"
        else:
            warning = audio_message

    pdf_exists = os.path.exists("story.pdf")
    return render_template(
        "story.html",
        story=story,
        audio_exists=audio_exists,
        pdf_exists=pdf_exists,
        warning=warning,
        genre=genre,
        setting=setting,
        tone=tone,
        language=language,
        read_minutes=read_minutes,
        word_count=word_count,
    )

@app.route('/download_pdf')
def download_pdf():
    if not os.path.exists("story.pdf"):
        return "PDF not available yet. Generate a story first.", 404
    return send_file("story.pdf", as_attachment=True)

# ---------------- MAIN ---------------- #
if __name__ == '__main__':
    app.run(debug=True)
