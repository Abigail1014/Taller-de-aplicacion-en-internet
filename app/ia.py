"""Cliente mínimo de Google Gemini (capa gratuita) vía API REST."""
import requests
from flask import current_app

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


class IAError(Exception):
    """Error amigable para mostrar al usuario."""


def consultar_gemini(prompt, temperatura=0.4):
    clave = current_app.config.get("GEMINI_API_KEY")
    if not clave:
        raise IAError(
            "Falta GEMINI_API_KEY. Créala gratis en https://aistudio.google.com/apikey "
            "y colócala en el archivo .env."
        )
    modelo = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        r = requests.post(
            URL.format(modelo=modelo),
            headers={"x-goog-api-key": clave, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperatura},
            },
            timeout=45,
        )
    except requests.RequestException as e:
        raise IAError(f"No se pudo conectar con Gemini: {e}")

    if r.status_code == 429:
        raise IAError("Se alcanzó el límite gratuito de Gemini. Espera un minuto e intenta de nuevo.")
    if r.status_code != 200:
        raise IAError(f"Gemini respondió con error {r.status_code}: {r.text[:200]}")
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, ValueError):
        raise IAError("Gemini no devolvió una respuesta válida (puede haber sido bloqueada).")
