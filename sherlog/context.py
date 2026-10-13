"""Baglam toplayici: bir uyariyla ilgili log satirlarini depodan ceker ve
SHAP nedenleriyle birlestirip dil modeline verilecek istemi hazirlar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .store import Kayit, KayitDeposu


@dataclass
class Uyari:
    uyari_id: str
    kaynak_ip: str
    zaman: str
    skor: float
    model: str
    shap_nedenleri: list[dict] = field(default_factory=list)


@dataclass
class Baglam:
    uyari: Uyari
    kayitlar: list[Kayit]

    @property
    def kayit_nolari(self) -> set[str]:
        return {k.kayit_no for k in self.kayitlar}


def baglam_topla(depo: KayitDeposu, uyari: Uyari, pencere_dk: int = 5, en_fazla: int = 50) -> Baglam:
    """Uyarinin kaynak IP'sine ait, uyari aninin +/- pencere_dk dakikasindaki kayitlari getirir."""
    t = datetime.fromisoformat(uyari.zaman)
    bas = (t - timedelta(minutes=pencere_dk)).isoformat(timespec="seconds")
    bit = (t + timedelta(minutes=pencere_dk)).isoformat(timespec="seconds")
    kayitlar = depo.ip_ve_aralik(uyari.kaynak_ip, bas, bit)[:en_fazla]
    return Baglam(uyari=uyari, kayitlar=kayitlar)


SISTEM_ISTEMI = """Sen bir guvenlik operasyon merkezi analistine yardim eden asistansin.
Yalnizca sana verilen log kayitlarina dayanarak Turkce bir olay ozeti yaz.
Kurallar:
1. Her cumlenin sonuna dayandigi kayit numarasini koseli parantezle yaz, ornek: [L0002] veya [L0002, L0005].
2. Kayitlarda olmayan IP, port, zaman ya da sayi YAZMA.
3. Emin olmadigin konuda tahmin yurutme; "kayitlardan anlasilmiyor" de.
4. Uc baslik kullan: Ne oldu, Neden supheli, Onerilen adimlar."""


def istem_olustur(b: Baglam) -> str:
    nedenler = "\n".join(
        f"- {n['oznitelik']} = {n['deger']} (etki {n['etki']:+.2f})" for n in b.uyari.shap_nedenleri
    )
    satirlar = "\n".join(k.metin() for k in b.kayitlar)
    return (
        f"Uyari {b.uyari.uyari_id}: {b.uyari.kaynak_ip} kaynakli trafik, model skoru {b.uyari.skor:.2f} "
        f"({b.uyari.model}).\n\n"
        f"Modelin kararini en cok etkileyen oznitelikler (SHAP):\n{nedenler}\n\n"
        f"Ilgili log kayitlari:\n{satirlar}\n\n"
        "Bu kayitlara dayanarak olay ozetini yaz."
    )
