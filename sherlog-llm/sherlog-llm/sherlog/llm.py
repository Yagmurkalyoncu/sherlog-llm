"""Yerel dil modeli istemcisi (Ollama). Veri makineden disari cikmaz:
istekler yalnizca localhost'taki Ollama sunucusuna gider."""

from __future__ import annotations

import json
import os
import urllib.request

VARSAYILAN_MODEL = os.environ.get("SHERLOG_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


class OllamaIstemcisi:
    def __init__(self, model: str = VARSAYILAN_MODEL, url: str = OLLAMA_URL, zaman_asimi: int = 300) -> None:
        self.model = model
        self.url = url.rstrip("/")
        self.zaman_asimi = zaman_asimi

    def uret(self, sistem: str, istem: str) -> str:
        govde = {
            "model": self.model,
            "system": sistem,
            "prompt": istem,
            "stream": False,
            # Tekrarlanabilirlik icin deterministik ayarlar.
            "options": {"temperature": 0, "seed": 42},
        }
        istek = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps(govde).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(istek, timeout=self.zaman_asimi) as yanit:
            return json.loads(yanit.read())["response"]


class SahteIstemci:
    """Ollama kurulu olmayan ortamlarda (testler, CI) kullanilan sabit cevapli istemci."""

    def __init__(self, cevap: str) -> None:
        self.cevap = cevap
        self.model = "sahte"

    def uret(self, sistem: str, istem: str) -> str:
        return self.cevap
