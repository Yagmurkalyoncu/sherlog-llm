"""Kayit deposu: her log satirina kalici bir kayit numarasi ve SHA-256 hash verir.

Ozetteki her cumle bu depodaki bir kayda atif yapar; analist de ayni depodan
ham kayda ulasir. Bu nedenle depo, iki katmanin ortak "tek dogru kaynagi"dir.
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ALANLAR = ["zaman", "kaynak_ip", "hedef_ip", "hedef_port", "protokol", "bayrak", "bayt", "sure_ms"]


@dataclass(frozen=True)
class Kayit:
    kayit_no: str
    zaman: str
    kaynak_ip: str
    hedef_ip: str
    hedef_port: int
    protokol: str
    bayrak: str
    bayt: int
    sure_ms: int
    ham: str
    sha256: str

    def metin(self) -> str:
        """Dil modeline verilecek tek satirlik gosterim."""
        return (
            f"[{self.kayit_no}] {self.zaman} {self.kaynak_ip} -> {self.hedef_ip}:{self.hedef_port} "
            f"{self.protokol} {self.bayrak} bayt={self.bayt} sure_ms={self.sure_ms}"
        )


class KayitDeposu:
    def __init__(self, yol: str | Path = ":memory:") -> None:
        self.db = sqlite3.connect(str(yol))
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS kayitlar (
                kayit_no TEXT PRIMARY KEY,
                zaman TEXT, kaynak_ip TEXT, hedef_ip TEXT, hedef_port INTEGER,
                protokol TEXT, bayrak TEXT, bayt INTEGER, sure_ms INTEGER,
                ham TEXT, sha256 TEXT)"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS ix_ip_zaman ON kayitlar(kaynak_ip, zaman)")

    def csv_yukle(self, csv_yolu: str | Path) -> int:
        """CSV log dosyasini okur; her satira L0001 biciminde numara verir."""
        mevcut = self.db.execute("SELECT COUNT(*) FROM kayitlar").fetchone()[0]
        eklenen = 0
        with open(csv_yolu, newline="", encoding="utf-8") as f:
            for satir in csv.DictReader(f):
                ham = ",".join(satir[a] for a in ALANLAR)
                no = f"L{mevcut + eklenen + 1:04d}"
                self.db.execute(
                    "INSERT INTO kayitlar VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        no, satir["zaman"], satir["kaynak_ip"], satir["hedef_ip"],
                        int(satir["hedef_port"]), satir["protokol"], satir["bayrak"],
                        int(satir["bayt"]), int(satir["sure_ms"]),
                        ham, hashlib.sha256(ham.encode("utf-8")).hexdigest(),
                    ),
                )
                eklenen += 1
        self.db.commit()
        return eklenen

    def getir(self, kayit_no: str) -> Kayit | None:
        r = self.db.execute("SELECT * FROM kayitlar WHERE kayit_no = ?", (kayit_no,)).fetchone()
        return Kayit(**dict(r)) if r else None

    def ip_ve_aralik(self, ip: str, baslangic: str, bitis: str) -> list[Kayit]:
        """Bir kaynak IP'nin verilen zaman araligindaki tum kayitlari (ISO zaman)."""
        rows = self.db.execute(
            "SELECT * FROM kayitlar WHERE kaynak_ip = ? AND zaman BETWEEN ? AND ? ORDER BY zaman, kayit_no",
            (ip, baslangic, bitis),
        ).fetchall()
        return [Kayit(**dict(r)) for r in rows]
