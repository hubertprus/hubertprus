"""
Vertex Quant Core – Gemini AI Studio Client
Moduł integracji z Google AI Studio (Gemini API).
"""

import os
import json
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

# Konfiguracja modelu
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# System prompt dla agenta Vertex Quant Core
VERTEX_QUANT_SYSTEM_PROMPT = """Jesteś wyspecjalizowanym agentem AI systemu Vertex Quant Core.
Twój twórca to programista i pasjonat technologii łączący architekturę Google Cloud,
automatyzację AI oraz produkcję muzyki elektronicznej.
Pomagasz w budowaniu platformy, generowaniu kodu, automatyzacji infrastruktury
oraz projektowaniu narzędzi wspierających produkcję muzyczną.
Odpowiadaj precyzyjnie, technicznie i po polsku, chyba że użytkownik pyta po angielsku."""


def get_gemini_client():
    """Inicjalizuje i zwraca skonfigurowany model Gemini."""
    if not GOOGLE_AI_API_KEY:
        raise ValueError(
            "Brak klucza GOOGLE_AI_API_KEY. "
            "Ustaw go w pliku .env: GOOGLE_AI_API_KEY=twój_klucz"
        )
    genai.configure(api_key=GOOGLE_AI_API_KEY)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=VERTEX_QUANT_SYSTEM_PROMPT,
    )


def chat_with_gemini(message: str, history: Optional[list] = None) -> str:
    """
    Wysyła wiadomość do Gemini i zwraca odpowiedź tekstową.

    Args:
        message: Wiadomość użytkownika.
        history: Opcjonalna historia konwersacji w formacie
                 [{"role": "user"/"model", "parts": ["tekst"]}]

    Returns:
        Odpowiedź modelu jako string.
    """
    model = get_gemini_client()

    if history:
        chat_session = model.start_chat(history=history)
    else:
        chat_session = model.start_chat()

    response = chat_session.send_message(message)
    return response.text


def generate_music_sequence(
    genre: str,
    bpm: int = 128,
    steps: int = 16,
    scale: str = "minor",
    key: str = "A",
) -> dict:
    """
    Generuje sekwencję muzyczną (nuty/kroki) dla podanego gatunku przez Gemini.

    Args:
        genre: Gatunek muzyczny (np. "techno", "trance", "deep house").
        bpm:   Tempo w BPM.
        steps: Liczba kroków sekwencji (16 lub 32).
        scale: Skala muzyczna ("minor" / "major").
        key:   Tonacja (np. "A", "C#", "F").

    Returns:
        Słownik z sekwencją, parametrami i opisem.
    """
    model = get_gemini_client()

    prompt = f"""Wygeneruj sekwencję muzyczną w formacie JSON dla:
- Gatunek: {genre}
- Tempo: {bpm} BPM
- Liczba kroków: {steps}
- Skala: {scale}
- Tonacja: {key}

Zwróć TYLKO poprawny JSON (bez markdown, bez komentarzy) w następującym formacie:
{{
  "genre": "{genre}",
  "bpm": {bpm},
  "key": "{key}",
  "scale": "{scale}",
  "steps": {steps},
  "kick_pattern": [lista {steps} wartości 0 lub 1],
  "snare_pattern": [lista {steps} wartości 0 lub 1],
  "hihat_pattern": [lista {steps} wartości 0 lub 1],
  "bass_notes": [lista {steps} nut jako string lub null, np. "A2", null, "C3"],
  "lead_notes": [lista {steps} nut jako string lub null],
  "description": "krótki opis charakteru sekwencji"
}}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Usuń ewentualne bloki markdown ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Zwróć odpowiedź tekstową jeśli JSON się nie udał
        return {"raw_response": raw, "error": "Nie udało się sparsować JSON"}


def analyze_audio_params(description: str) -> dict:
    """
    Analizuje i sugeruje parametry audio/syntezatora na podstawie opisu.

    Args:
        description: Opis dźwięku lub brzmienia (np. "ciepły bas techno z distortionem").

    Returns:
        Słownik z sugerowanymi parametrami syntezatora.
    """
    model = get_gemini_client()

    prompt = f"""Zaproponuj parametry syntezatora dla: "{description}"

Zwróć TYLKO poprawny JSON (bez markdown):
{{
  "oscillator": {{
    "waveform": "sawtooth|square|sine|triangle",
    "detune_cents": liczba od -100 do 100
  }},
  "filter": {{
    "type": "lowpass|highpass|bandpass",
    "cutoff_hz": liczba,
    "resonance": liczba od 0 do 1
  }},
  "envelope": {{
    "attack_ms": liczba,
    "decay_ms": liczba,
    "sustain": liczba od 0 do 1,
    "release_ms": liczba
  }},
  "effects": {{
    "reverb_mix": liczba od 0 do 1,
    "delay_ms": liczba,
    "distortion": liczba od 0 do 1
  }},
  "description": "opis brzmienia"
}}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "error": "Nie udało się sparsować JSON"}
