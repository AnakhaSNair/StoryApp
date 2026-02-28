# KathaAI StoryApp

A Flask app that generates stories from your prompt and provides:
- AI story generation (Hugging Face Router)
- Offline fallback story mode when API is unavailable
- Audio narration (`gTTS`)
- PDF export (`reportlab`)
- Reading-time and word-count metadata
- English and Malayalam story support

## Screenshots

![OUR STORIES!!!](Screenshots/Screenshot%202026-02-28%20100832.png)
![OUR STORIES!!!](Screenshots/Screenshot%202026-02-28%20100858.png)
![OUR STORIES!!!](Screenshots/Screenshot%202026-02-28%20100912.png)

## Project Structure

```text
StoryApp/
- app.py
- requirements.txt
- templates/
  - layout.html
  - landing.html
  - index.html
  - story.html
- static/
  - style.css
  - audio/
    - story.mp3 (generated)
```

## Requirements

- Python 3.10+
- Internet access for:
  - Hugging Face Router (AI story generation)
  - Google TTS (audio generation)

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in project root:

```env
HF_API_KEY=your_huggingface_token_here
```

If `HF_API_KEY` is missing/invalid, the app still works using offline fallback story mode.

## Run

```powershell
python app.py
```

Open: `http://127.0.0.1:5000`

## How It Works

1. Go to `/create`
2. Fill in genre, characters, setting, tone, language, and length
3. Submit to generate a story
4. The app also attempts to generate:
   - `static/audio/story.mp3`
   - `story.pdf`
5. Download PDF from `/download_pdf`

## Main Routes

- `/` -> Landing page
- `/create` -> Story input form
- `/generate` (`POST`) -> Generates story + metadata + audio + PDF
- `/download_pdf` -> Downloads generated PDF

## Notes

- `story.pdf` and `static/audio/story.mp3` are overwritten on each new generation.
- If Google TTS is unreachable, story generation still succeeds and a warning is shown.
- If Hugging Face API fails, offline fallback text is generated automatically.
