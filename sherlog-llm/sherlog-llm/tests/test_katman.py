import json
import unittest
from pathlib import Path

from sherlog.context import Uyari, baglam_topla, istem_olustur
from sherlog.store import KayitDeposu
from sherlog.verifier import cumlelere_bol, dogrula

KOK = Path(__file__).resolve().parent.parent


def kur():
    depo = KayitDeposu()
    depo.csv_yukle(KOK / "data" / "ornek_loglar.csv")
    uyari = Uyari(**json.loads((KOK / "data" / "ornek_uyari.json").read_text(encoding="utf-8")))
    return depo, baglam_topla(depo, uyari)


class DepoTesti(unittest.TestCase):
    def test_kayit_numarasi_ve_hash(self):
        depo, _ = kur()
        k = depo.getir("L0002")
        self.assertEqual((k.kaynak_ip, k.hedef_port), ("10.0.0.23", 22))
        self.assertEqual(len(k.sha256), 64)


class BaglamTesti(unittest.TestCase):
    def test_yalnizca_ilgili_ip_ve_pencere(self):
        _, b = kur()
        self.assertEqual({k.kaynak_ip for k in b.kayitlar}, {"10.0.0.23"})
        # 14:21 kaydi 5 dakikalik pencerenin disinda kalmali.
        self.assertNotIn("L0014", b.kayit_nolari)
        self.assertEqual(len(b.kayitlar), 10)

    def test_istem_kayit_numaralarini_ve_shap_icerir(self):
        _, b = kur()
        istem = istem_olustur(b)
        self.assertIn("[L0002]", istem)
        self.assertIn("farkli_hedef_port_sayisi", istem)


class DogrulayiciTesti(unittest.TestCase):
    def setUp(self):
        _, self.b = kur()

    def test_dogru_cumle_gecer(self):
        s = dogrula("Ilk deneme 10.0.0.5 hedefinin port 22 adresine 14:03:05 saatinde yapildi [L0002].", self.b.kayitlar)
        self.assertTrue(s.cumleler[0].gecerli, s.cumleler[0].sorunlar)

    def test_atifsiz_cumle_isaretlenir(self):
        s = dogrula("Saldirgan sisteme sizdi.", self.b.kayitlar)
        self.assertIn("atif yok", s.cumleler[0].sorunlar)

    def test_kayitta_olmayan_ip_isaretlenir(self):
        s = dogrula("Kaynak 10.0.0.7 adresine erisim denedi [L0004].", self.b.kayitlar)
        self.assertFalse(s.cumleler[0].gecerli)

    def test_yanlis_port_isaretlenir(self):
        s = dogrula("Deneme port 21 uzerinden yapildi [L0002].", self.b.kayitlar)
        self.assertIn("port kayitta yok: 21", s.cumleler[0].sorunlar)

    def test_baglam_disi_kayit_isaretlenir(self):
        s = dogrula("Daha sonra normal trafik goruldu [L0014].", self.b.kayitlar)
        self.assertFalse(s.cumleler[0].gecerli)

    def test_basliklar_cumle_sayilmaz(self):
        self.assertEqual(cumlelere_bol("Ne oldu:\nBir tarama yapildi [L0002]."), ["Bir tarama yapildi [L0002]."])


if __name__ == "__main__":
    unittest.main()
