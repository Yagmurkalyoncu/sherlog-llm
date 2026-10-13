"""Dogrulayici: ozetteki her cumlenin atif yaptigi kayitlara gercekten dayanip
dayanmadigini kural tabanli olarak kontrol eder.

Kontroller:
- Cumlede atif ([L0001]) var mi?
- Atif yapilan kayit numaralari baglamda var mi?
- Cumledeki IP, port ve saat degerleri atif yapilan kayitlarda geciyor mu?
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .store import Kayit

ATIF = re.compile(r"\[(L\d{4}(?:\s*,\s*L\d{4})*)\]")
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
PORT = re.compile(r"\bport\w*\s+(\d{1,5})\b", re.IGNORECASE)
IP_PORT = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:(\d{1,5})\b")
SAAT = re.compile(r"\b(\d{2}:\d{2}(?::\d{2})?)\b")
BASLIK = re.compile(r"^\s*(#+\s*)?[\w\s]+:\s*$")


@dataclass
class CumleSonucu:
    cumle: str
    atiflar: list[str]
    sorunlar: list[str] = field(default_factory=list)

    @property
    def gecerli(self) -> bool:
        return not self.sorunlar


@dataclass
class DogrulamaSonucu:
    cumleler: list[CumleSonucu]

    @property
    def gecerli_oran(self) -> float:
        return sum(c.gecerli for c in self.cumleler) / len(self.cumleler) if self.cumleler else 0.0

    @property
    def hatali(self) -> list[CumleSonucu]:
        return [c for c in self.cumleler if not c.gecerli]


def cumlelere_bol(metin: str) -> list[str]:
    parcalar: list[str] = []
    for satir in metin.splitlines():
        satir = satir.strip().lstrip("-*•").strip()
        if not satir or BASLIK.match(satir):
            continue
        # Nokta, unlem, soru isaretinden (ve ardindan gelen atiftan) sonra bol.
        for c in re.split(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])", satir):
            if c.strip():
                parcalar.append(c.strip())
    return parcalar


def _kayit_metni(kayitlar: list[Kayit]) -> str:
    return " ".join(f"{k.zaman} {k.kaynak_ip} {k.hedef_ip} {k.hedef_port}" for k in kayitlar)


def dogrula(ozet: str, kayitlar: list[Kayit]) -> DogrulamaSonucu:
    sozluk = {k.kayit_no: k for k in kayitlar}
    sonuclar = []
    for cumle in cumlelere_bol(ozet):
        atiflar = [no.strip() for grup in ATIF.findall(cumle) for no in grup.split(",")]
        s = CumleSonucu(cumle=cumle, atiflar=atiflar)
        if not atiflar:
            s.sorunlar.append("atif yok")
            sonuclar.append(s)
            continue
        bilinmeyen = [a for a in atiflar if a not in sozluk]
        if bilinmeyen:
            s.sorunlar.append(f"baglamda olmayan kayit: {', '.join(bilinmeyen)}")
        dayanak = _kayit_metni([sozluk[a] for a in atiflar if a in sozluk])
        govde = ATIF.sub("", cumle)
        for ip in IP.findall(govde):
            if ip not in dayanak:
                s.sorunlar.append(f"IP kayitta yok: {ip}")
        for port in PORT.findall(govde) + IP_PORT.findall(govde):
            if f" {port}" not in f" {dayanak}":
                s.sorunlar.append(f"port kayitta yok: {port}")
        for saat in SAAT.findall(govde):
            if f"T{saat}" not in dayanak:
                s.sorunlar.append(f"saat kayitta yok: {saat}")
        sonuclar.append(s)
    return DogrulamaSonucu(cumleler=sonuclar)
