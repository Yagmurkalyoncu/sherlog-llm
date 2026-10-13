"""Uctan uca demo: log -> kayit deposu -> baglam -> yerel LLM -> dogrulama.

Kullanim:
    python demo.py              # Ollama (varsayilan model qwen2.5:7b) ile
    python demo.py --sahte      # Ollama olmadan, sabit ornek cevapla
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sherlog.context import SISTEM_ISTEMI, Uyari, baglam_topla, istem_olustur
from sherlog.llm import OllamaIstemcisi, SahteIstemci
from sherlog.store import KayitDeposu
from sherlog.verifier import dogrula

KOK = Path(__file__).parent

ORNEK_CEVAP = """Ne oldu:
10.0.0.23 adresi 14:03:05 ile 14:03:08 arasinda 10.0.0.5 hedefinin 10 farkli portuna SYN paketi gonderdi [L0002, L0011].
Ilk baglanti denemesi port 22 uzerinden yapildi [L0002].

Neden supheli:
Paketlerin tamami 60 bayt ve baglanti sureleri 1 ms; bu, port taramasiyla uyumlu bir davranistir [L0002, L0011].
Ayni kaynak daha once 10.0.0.7 adresine de erisim denedi [L0004].

Onerilen adimlar:
10.0.0.23 kaynakli trafigi gecici olarak sinirlayin ve 10.0.0.5 uzerindeki 3389 portunun erisim kayitlarini inceleyin [L0010].
"""


def main() -> None:
    p = argparse.ArgumentParser(description="Sherlog dil modeli katmani demosu")
    p.add_argument("--sahte", action="store_true", help="Ollama yerine sabit ornek cevap kullan")
    p.add_argument("--model", default=None, help="Ollama model adi (varsayilan: qwen2.5:7b)")
    a = p.parse_args()

    depo = KayitDeposu()
    n = depo.csv_yukle(KOK / "data" / "ornek_loglar.csv")
    uyari = Uyari(**json.loads((KOK / "data" / "ornek_uyari.json").read_text(encoding="utf-8")))
    baglam = baglam_topla(depo, uyari)

    print(f"{n} kayit yuklendi; uyari {uyari.uyari_id} icin {len(baglam.kayitlar)} ilgili kayit bulundu.\n")

    if a.sahte:
        istemci = SahteIstemci(ORNEK_CEVAP)
    else:
        istemci = OllamaIstemcisi(model=a.model) if a.model else OllamaIstemcisi()
    ozet = istemci.uret(SISTEM_ISTEMI, istem_olustur(baglam))

    print(f"--- Olay ozeti ({istemci.model}) ---\n{ozet.strip()}\n")
    sonuc = dogrula(ozet, baglam.kayitlar)
    print(f"--- Dogrulama: {len(sonuc.cumleler)} cumlenin %{100 * sonuc.gecerli_oran:.0f}'i kayitlara dayaniyor ---")
    for c in sonuc.hatali:
        print(f"[ISARETLENDI] {c.cumle}\n    -> {'; '.join(c.sorunlar)}")


if __name__ == "__main__":
    main()
