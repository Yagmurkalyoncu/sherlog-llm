# Sherlog · Dil Modeli Katmanı

Sherlog, güvenlik kayıtlarında anomali tespiti yapan ve tespit edilen olayları **yerel bir dil modeliyle, her cümlesi kaynak kayda atıflı Türkçe özetlerle** açıklayan bir sistemdir. Bu repo, sistemin **dil modeli katmanının** çalışan ilk sürümüdür: bağlam toplayıcı, yerel LLM istemcisi ve doğrulayıcı.

Tüm bileşenler internetsiz tek bir makinede çalışır; dil modeline yapılan istekler yalnızca `localhost` üzerindeki Ollama sunucusuna gider.

## Mimarideki yeri

```
Tespit katmanı (ML + SHAP)                    Dil modeli katmanı (bu repo)
──────────────────────────                    ─────────────────────────────────────────────
log → ön işleme → kayıt deposu ──────────────► bağlam toplayıcı → yerel LLM → doğrulayıcı → analist
                  (L0001, L0002 …)    uyarı +   (aynı IP, ±5 dk)   (Ollama,     (IP/port/saat
                                      SHAP      + SHAP nedenleri    Qwen)        atıf kontrolü)
```

Dil modeli **hesap yapmaz, yorumlar**: hangi kayıtların ilgili olduğunu deterministik bir sorgu belirler, model yalnızca bu kayıtları özetler.

## Bileşenler

| Modül | Görevi |
| --- | --- |
| `sherlog/store.py` | Log satırlarını SQLite'a yazar; her satıra kalıcı kayıt numarası (`L0001`) ve SHA-256 hash verir. |
| `sherlog/context.py` | Uyarının kaynak IP'sine ait, ±5 dakikalık penceredeki kayıtları çeker; SHAP nedenleriyle birlikte istemi hazırlar. |
| `sherlog/llm.py` | Ollama istemcisi (varsayılan `qwen2.5:7b`, `temperature=0`, sabit seed). Testler için sahte istemci içerir. |
| `sherlog/verifier.py` | Özeti cümlelere böler; atıfı olmayan cümleyi ve atıf yapılan kayıtta geçmeyen IP, port veya saati işaretler. |

## Çalıştırma

Python 3.10+ yeterlidir; harici bağımlılık yoktur.

```bash
# 1) Ollama olmadan, örnek bir cevapla uçtan uca akış
python demo.py --sahte

# 2) Yerel modelle
ollama pull qwen2.5:7b
python demo.py                     # veya: python demo.py --model qwen2.5:3b

# Testler
python -m unittest discover -s tests -t .
```

Örnek çıktı (`--sahte`): doğrulayıcı, kayıtlarda geçmeyen bir IP adresini içeren cümleyi yakalar.

```
14 kayit yuklendi; uyari U-0001 icin 10 ilgili kayit bulundu.
...
--- Dogrulama: 5 cumlenin %80'i kayitlara dayaniyor ---
[ISARETLENDI] Ayni kaynak daha once 10.0.0.7 adresine de erisim denedi [L0004].
    -> IP kayitta yok: 10.0.0.7
```

`data/` altındaki log ve uyarı dosyaları, akışı göstermek için hazırlanmış **sentetik** örneklerdir (bir port taraması senaryosu).

## Durum ve yol haritası

- [x] Kayıt numaralı ve hash'li kayıt deposu
- [x] Bağlam toplayıcı (IP + zaman penceresi) ve SHAP nedenlerini içeren istem
- [x] Ollama üzerinden yerel model istemcisi
- [x] Kural tabanlı doğrulayıcı (atıf, IP, port, saat) ve birim testleri
- [ ] Açık veri setlerinden (CIC-IDS2017, UNSW-NB15 vb.) gerçek log alımı
- [ ] Tespit katmanından gelen uyarı biçimiyle entegrasyon
- [ ] Doğrulanamayan cümlede özeti bir kez yeniden üretme
- [ ] Sayı ve süre iddialarının doğrulanması
- [ ] Atıf doğruluğu ve özet süresi ölçümleri
- [ ] Analist arayüzü (Streamlit)

## Ekip

Ankara Üniversitesi Bilgisayar Mühendisliği · Sherlog ekibi

- Yağmur Kalyoncu: dil modeli katmanı (bu repo)
- Halime Şahnur Çöğür: tespit katmanı
