"""Tek seferlik: kataloğa çok sayıda araç ekler (duplicate kontrollü).

catalog_data.json'a yeni araçları ekler; (make, model, vehicle_type) zaten varsa
atlar. Spec değerleri temel/web-doğrulanmış; parça no'ları "örnek:" yer tutucu —
el kitabına/parça kataloğuna karşı doğrulanmalı. LPG araçlarında LPG sistemine
müdahale TARİFİ YOK (yalnızca temel bakım verisi).
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "domain" / "catalog_data.json"
rows = json.loads(DATA.read_text(encoding="utf-8"))


def spec(
    oil_spec=None,
    oil_capacity_l=None,
    oil_drain_bolt_size=None,
    oil_drain_location="yağ karteri alt orta",
    oil_filter_part=None,
    air_filter_part=None,
    cabin_filter_part=None,
    spark_plug_part=None,
    battery_spec=None,
    battery_location="motor bölmesi sol ön",
    transmission_type=None,
):
    return {
        "oil_spec": oil_spec,
        "oil_capacity_l": oil_capacity_l,
        "oil_drain_bolt_size": oil_drain_bolt_size,
        "oil_drain_location": oil_drain_location,
        "oil_filter_part": oil_filter_part,
        "air_filter_part": air_filter_part,
        "cabin_filter_part": cabin_filter_part,
        "spark_plug_part": spark_plug_part,
        "battery_spec": battery_spec,
        "battery_location": battery_location,
        "transmission_type": transmission_type,
    }


def car(make, model, ymin, ymax, fuels, s, engine_codes=()):
    return {
        "make": make,
        "model": model,
        "year_min": int(ymin),
        "year_max": int(ymax),
        "vehicle_type": "araba",
        "fuels": list(fuels),
        "engine_codes": list(engine_codes),
        "spec": s,
    }


EV = lambda **kw: spec(  # noqa: E731 — elektrikli araç spec yardımcısı
    oil_spec=None,
    oil_capacity_l=None,
    oil_drain_bolt_size=None,
    oil_drain_location=None,
    oil_filter_part=None,
    air_filter_part=None,
    spark_plug_part=None,
    **kw,
)

NEW = [
    # --- Mevcut markalara DAHA FAZLA model ---
    car("Volkswagen", "Caddy", 2011, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00)", 4.3, "19mm", oil_filter_part="örnek: 04L115562", air_filter_part="örnek: 2K0129620", cabin_filter_part="örnek: 1T0819644B", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Volkswagen", "Transporter", 2010, 2024, ["dizel"], spec("5W-30 (VW 507.00)", 6.5, "19mm", oil_filter_part="örnek: 070115562", air_filter_part="örnek: 7H0129620", cabin_filter_part="örnek: 7H0819631A", spark_plug_part=None, battery_spec="70-95Ah", battery_location="koltuk altı", transmission_type="manuel / DSG")),
    car("Volkswagen", "T-Roc", 2017, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00)", 4.3, "19mm", oil_filter_part="örnek: 04E115561H", air_filter_part="örnek: 5Q0129620D", cabin_filter_part="örnek: 5Q0819669", spark_plug_part="örnek: NGK 04E905602D (benzin)", battery_spec="60-70Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Renault", "Kadjar", 2015, 2022, ["benzin", "dizel"], spec("5W-40", 4.5, "10mm", oil_filter_part="örnek: 152089599R", air_filter_part="örnek: 165466455R", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK LZKAR6AP-11 (benzin)", battery_spec="60Ah / 540A", battery_location="motor bölmesi sağ ön", transmission_type="manuel / EDC")),
    car("Renault", "Talisman", 2016, 2022, ["benzin", "dizel"], spec("5W-40", 5.4, "10mm", oil_filter_part="örnek: 152089599R", air_filter_part="örnek: 165466455R", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah", battery_location="motor bölmesi sağ ön", transmission_type="EDC otomatik")),
    car("Fiat", "Doblo", 2010, 2024, ["dizel", "benzin"], spec("5W-40", 4.3, "14mm", oil_filter_part="örnek: 55256470", air_filter_part="örnek: 51897064", cabin_filter_part="örnek: 77367464", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah / 540A", transmission_type="manuel")),
    car("Fiat", "500", 2008, 2024, ["benzin", "hibrit", "elektrik"], spec("5W-40", 2.8, "14mm", oil_filter_part="örnek: 55256470", air_filter_part="örnek: 51897064", cabin_filter_part="örnek: 77367464", spark_plug_part="örnek: NGK (benzin)", battery_spec="50Ah / 500e yüksek voltaj", transmission_type="manuel / otomatik / elektrikli")),
    car("Toyota", "C-HR", 2016, 2024, ["benzin", "hibrit"], spec("0W-20", 4.2, "14mm", oil_filter_part="örnek: 04152-YZZA1", air_filter_part="örnek: 17801-0T050", cabin_filter_part="örnek: 87139-0N010", spark_plug_part="örnek: Denso (benzin)", battery_spec="45-60Ah / hibrit yardımcı", battery_location="motor bölmesi / bagaj (hibrit)", transmission_type="e-CVT (hibrit) / CVT")),
    car("Toyota", "Auris", 2012, 2018, ["benzin", "hibrit", "dizel"], spec("0W-20 / 5W-30", 4.2, "14mm", oil_filter_part="örnek: 04152-YZZA1", air_filter_part="örnek: 17801-0T050", cabin_filter_part="örnek: 87139-0N010", spark_plug_part="örnek: Denso (benzin)", battery_spec="45-60Ah", battery_location="motor bölmesi / bagaj (hibrit)", transmission_type="manuel / CVT / e-CVT")),
    car("Toyota", "Hilux", 2015, 2024, ["dizel"], spec("5W-30", 7.5, "14mm", oil_filter_part="örnek: 04152-YZZA6", air_filter_part="örnek: 17801-0L040", cabin_filter_part="örnek: 87139-0K080", spark_plug_part=None, battery_spec="70-80Ah", transmission_type="manuel / otomatik")),
    car("Hyundai", "Elantra", 2011, 2024, ["benzin"], spec("5W-30", 3.6, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-3X000", cabin_filter_part="örnek: 97133-3X000", spark_plug_part="örnek: NGK SILZKR6B-10E", battery_spec="60Ah / 540A", transmission_type="manuel / otomatik")),
    car("Hyundai", "Bayon", 2021, 2024, ["benzin"], spec("5W-30", 3.6, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-Q5100", cabin_filter_part="örnek: 97133-K2000", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah", transmission_type="manuel / DCT")),
    car("Hyundai", "Kona", 2017, 2024, ["benzin", "hibrit", "elektrik"], spec("5W-30", 3.6, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-J9000", cabin_filter_part="örnek: 97133-J9000", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah / Kona Electric yüksek voltaj", transmission_type="DCT / otomatik / elektrikli")),
    car("Kia", "Rio", 2011, 2023, ["benzin"], spec("5W-30", 3.3, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-H8100", cabin_filter_part="örnek: 97133-H8100", spark_plug_part="örnek: NGK (benzin)", battery_spec="55Ah", transmission_type="manuel / otomatik")),
    car("Kia", "Stonic", 2017, 2024, ["benzin"], spec("5W-30", 3.6, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-H8100", cabin_filter_part="örnek: 97133-H8100", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah", transmission_type="manuel / DCT")),
    car("Kia", "Cerato", 2013, 2024, ["benzin"], spec("5W-30", 3.6, "17mm", oil_filter_part="örnek: 26300-35505", air_filter_part="örnek: 28113-A7100", cabin_filter_part="örnek: 97133-A7000", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah", transmission_type="manuel / otomatik")),
    car("Ford", "Courier", 2014, 2024, ["dizel", "benzin"], spec("5W-30", 4.1, "13mm iç altıgen (allen)", oil_filter_part="örnek: 1920QM", air_filter_part="örnek: 1848220", cabin_filter_part="örnek: 1812519", spark_plug_part="örnek: Motorcraft (benzin)", battery_spec="60Ah", transmission_type="manuel")),
    car("Ford", "Puma", 2019, 2024, ["benzin", "hibrit"], spec("5W-20", 4.3, "13mm iç altıgen (allen)", oil_filter_part="örnek: 2207059", air_filter_part="örnek: 2244850", cabin_filter_part="örnek: 2355514", spark_plug_part="örnek: Motorcraft (benzin)", battery_spec="60-70Ah (EFB)", transmission_type="manuel / otomatik")),
    car("Opel", "Insignia", 2010, 2022, ["benzin", "dizel"], spec("5W-30 (dexos2)", 5.5, "15mm", oil_filter_part="örnek: 55594651", air_filter_part="örnek: 13272719", cabin_filter_part="örnek: 13271190", spark_plug_part="örnek: NGK / ACDelco (benzin)", battery_spec="70Ah", transmission_type="manuel / otomatik")),
    car("Opel", "Mokka", 2012, 2024, ["benzin", "dizel"], spec("5W-30", 4.3, "15mm", oil_filter_part="örnek: 55594651", air_filter_part="örnek: 13367308", cabin_filter_part="örnek: 13356914", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", transmission_type="manuel / otomatik")),
    car("Peugeot", "2008", 2013, 2024, ["benzin", "dizel", "elektrik"], spec("0W-30 / 5W-30", 3.5, "örnek: Torx / 13mm", oil_filter_part="örnek: 1109AY", air_filter_part="örnek: 1444TT", cabin_filter_part="örnek: 6447XF", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah (EFB) / e-2008 yüksek voltaj", transmission_type="manuel / EAT8 / elektrikli")),
    car("Peugeot", "508", 2011, 2024, ["benzin", "dizel", "hibrit"], spec("0W-30 / 5W-30", 4.25, "örnek: Torx / 13mm", oil_filter_part="örnek: 1109CL", air_filter_part="örnek: 1444VR", cabin_filter_part="örnek: 6447XR", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah (EFB)", transmission_type="otomatik (EAT8)")),
    car("Citroen", "C4", 2010, 2024, ["benzin", "dizel", "elektrik"], spec("0W-30 / 5W-30", 3.75, "örnek: Torx / 13mm", oil_filter_part="örnek: 1109AY", air_filter_part="örnek: 1444TT", cabin_filter_part="örnek: 6447XF", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah / e-C4 yüksek voltaj", transmission_type="manuel / EAT8 / elektrikli")),
    car("Citroen", "Berlingo", 2010, 2024, ["dizel", "benzin"], spec("5W-30", 4.25, "örnek: Torx / 13mm", oil_filter_part="örnek: 1109AY", air_filter_part="örnek: 1444TT", cabin_filter_part="örnek: 6447XF", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", transmission_type="manuel / EAT8")),
    car("Dacia", "Sandero", 2021, 2024, ["benzin", "lpg"], spec("5W-40", 4.2, "10mm", oil_filter_part="örnek: 152089599R", air_filter_part="örnek: 165466455R", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK LZKAR6AP-11 (benzin)", battery_spec="60Ah", battery_location="motor bölmesi sağ ön", transmission_type="manuel / otomatik"), ("H4D",)),
    car("Dacia", "Jogger", 2022, 2024, ["benzin", "lpg", "hibrit"], spec("5W-40", 4.2, "10mm", oil_filter_part="örnek: 152089599R", air_filter_part="örnek: 165466455R", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK LZKAR6AP-11 (benzin)", battery_spec="60Ah", battery_location="motor bölmesi sağ ön", transmission_type="manuel / otomatik (hibrit)")),
    car("Nissan", "X-Trail", 2014, 2024, ["benzin", "dizel", "hibrit"], spec("5W-40", 4.8, "14mm", oil_filter_part="örnek: 15208-65F0E", air_filter_part="örnek: 16546-4BA1A", cabin_filter_part="örnek: 27277-4BA0A", spark_plug_part="örnek: NGK (benzin)", battery_spec="65Ah", transmission_type="Xtronic CVT")),
    car("Honda", "Jazz", 2011, 2024, ["benzin", "hibrit"], spec("0W-20 / 5W-30", 3.6, "14mm", oil_filter_part="örnek: 15400-RTA-003", air_filter_part="örnek: 17220-5R0-008", cabin_filter_part="örnek: 80292-T5A-J01", spark_plug_part="örnek: NGK (benzin)", battery_spec="45Ah / hibrit yardımcı", transmission_type="CVT / e-HEV")),
    car("Skoda", "Superb", 2010, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00)", 4.6, "19mm", oil_filter_part="örnek: 06L115562B", air_filter_part="örnek: 3Q0129620", cabin_filter_part="örnek: 3V0819644", spark_plug_part="örnek: NGK (benzin)", battery_spec="70-72Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Skoda", "Fabia", 2010, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00)", 3.9, "19mm", oil_filter_part="örnek: 03C115561H", air_filter_part="örnek: 6R0129620", cabin_filter_part="örnek: 6R0819653", spark_plug_part="örnek: NGK (benzin)", battery_spec="51-60Ah", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Skoda", "Karoq", 2017, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00)", 4.3, "19mm", oil_filter_part="örnek: 04E115561H", air_filter_part="örnek: 5Q0129620D", cabin_filter_part="örnek: 5Q0819669", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Audi", "A6", 2011, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00/507.00)", 6.3, "19mm", oil_filter_part="örnek: 06L115562B", air_filter_part="örnek: 4M0133843", cabin_filter_part="örnek: 4M0819439", spark_plug_part="örnek: NGK (benzin)", battery_spec="80Ah (AGM)", battery_location="bagaj", transmission_type="S tronic / tiptronic")),
    car("Audi", "Q3", 2011, 2024, ["benzin", "dizel"], spec("5W-30 (VW 504.00/507.00)", 4.6, "19mm", oil_filter_part="örnek: 06L115562B", air_filter_part="örnek: 8U0133843", cabin_filter_part="örnek: 8U0819439", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah (AGM)", transmission_type="S tronic")),
    car("BMW", "2 Serisi", 2014, 2024, ["benzin", "dizel"], spec("5W-30 (BMW LL-04)", 4.5, "8mm iç altıgen (allen)", oil_filter_part="örnek: 11428583898", air_filter_part="örnek: 13718580427", cabin_filter_part="örnek: 64319321046", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah (AGM)", battery_location="bagaj / motor bölmesi", transmission_type="manuel / otomatik")),
    car("BMW", "4 Serisi", 2013, 2024, ["benzin", "dizel"], spec("5W-30 (BMW LL-04)", 5.2, "8mm iç altıgen (allen)", oil_filter_part="örnek: 11428583898", air_filter_part="örnek: 13718511668", cabin_filter_part="örnek: 64119237555", spark_plug_part="örnek: NGK (benzin)", battery_spec="80Ah (AGM)", battery_location="bagaj", transmission_type="otomatik (ZF 8HP)")),
    car("BMW", "X1", 2012, 2024, ["benzin", "dizel"], spec("5W-30 (BMW LL-04)", 5.0, "8mm iç altıgen (allen)", oil_filter_part="örnek: 11428583898", air_filter_part="örnek: 13718580427", cabin_filter_part="örnek: 64319321046", spark_plug_part="örnek: NGK (benzin)", battery_spec="70-80Ah (AGM)", transmission_type="otomatik")),
    car("BMW", "X3", 2011, 2024, ["benzin", "dizel"], spec("5W-30 (BMW LL-04)", 6.5, "8mm iç altıgen (allen)", oil_filter_part="örnek: 11428575211", air_filter_part="örnek: 13717811026", cabin_filter_part="örnek: 64119248294", spark_plug_part="örnek: NGK (benzin)", battery_spec="80-90Ah (AGM)", battery_location="bagaj", transmission_type="otomatik (ZF 8HP)")),
    car("Mercedes-Benz", "GLC", 2015, 2024, ["benzin", "dizel"], spec("5W-30 (MB 229.51/229.52)", 6.5, "13mm", oil_filter_part="örnek: A6541800009", air_filter_part="örnek: A6540940404", cabin_filter_part="örnek: A2138300118", spark_plug_part="örnek: NGK (benzin)", battery_spec="80Ah (AGM)", battery_location="motor bölmesi", transmission_type="otomatik (9G-Tronic)")),
    car("Mercedes-Benz", "B-Serisi", 2011, 2024, ["benzin", "dizel"], spec("5W-30 (MB 229.51)", 5.5, "13mm", oil_filter_part="örnek: A2701800109", air_filter_part="örnek: A2700940204", cabin_filter_part="örnek: A2468300018", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", battery_location="motor bölmesi", transmission_type="otomatik (7G-DCT)")),
    car("Mercedes-Benz", "Vito", 2010, 2024, ["dizel"], spec("5W-30 (MB 229.51)", 8.0, "13mm", oil_filter_part="örnek: A6511800009", air_filter_part="örnek: A6510940204", cabin_filter_part="örnek: A4478350047", spark_plug_part=None, battery_spec="90-95Ah", battery_location="koltuk altı", transmission_type="otomatik")),
    # --- YENİ MARKALAR ---
    car("Cupra", "Formentor", 2020, 2024, ["benzin", "hibrit"], spec("5W-30 (VW 504.00)", 4.6, "19mm", oil_filter_part="örnek: 06L115562B", air_filter_part="örnek: 5Q0129620E", cabin_filter_part="örnek: 5Q0819669", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah (EFB/AGM)", battery_location="motor bölmesi sol arka", transmission_type="DSG")),
    car("Jeep", "Renegade", 2014, 2024, ["benzin", "dizel"], spec("5W-40", 4.3, "14mm", oil_filter_part="örnek: 68191349AA", air_filter_part="örnek: 51897064", cabin_filter_part="örnek: 77367464", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", transmission_type="manuel / otomatik")),
    car("Jeep", "Compass", 2017, 2024, ["benzin", "dizel", "hibrit"], spec("5W-40", 4.3, "14mm", oil_filter_part="örnek: 68191349AA", air_filter_part="örnek: 68249925AA", cabin_filter_part="örnek: 68223044AA", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", transmission_type="otomatik")),
    car("MG", "ZS", 2017, 2024, ["benzin", "elektrik"], spec("5W-30", 4.0, "14mm", oil_filter_part="örnek: 10372000", air_filter_part="örnek: 10220377", cabin_filter_part="örnek: 10172776", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah / ZS EV yüksek voltaj", transmission_type="otomatik / elektrikli")),
    car("MG", "4", 2022, 2024, ["elektrik"], EV(cabin_filter_part="örnek: kabin filtresi", battery_spec="12V yardımcı (ana batarya yüksek voltaj)", battery_location="ön/taban (HV batarya)", transmission_type="tek vitesli (elektrikli)")),
    car("BYD", "Atto 3", 2022, 2024, ["elektrik"], EV(cabin_filter_part="örnek: kabin filtresi", battery_spec="12V yardımcı (Blade batarya yüksek voltaj)", battery_location="taban (HV batarya)", transmission_type="tek vitesli (elektrikli)")),
    car("Tesla", "Model Y", 2020, 2024, ["elektrik"], EV(cabin_filter_part="örnek: 1107682-00-A (HEPA/kabin)", battery_spec="12V yardımcı akü (ana batarya yüksek voltaj)", battery_location="ön bagaj (12V) / taban (HV batarya)", transmission_type="tek vitesli (elektrikli)")),
    car("Subaru", "Forester", 2013, 2024, ["benzin"], spec("0W-20 / 5W-30", 4.8, "14mm", oil_filter_part="örnek: 15208AA15A", air_filter_part="örnek: 16546AA12A", cabin_filter_part="örnek: 72880FL000", spark_plug_part="örnek: NGK (benzin)", battery_spec="65Ah", transmission_type="Lineartronic CVT")),
    car("Volvo", "XC40", 2017, 2024, ["benzin", "dizel", "elektrik"], spec("0W-20 / 0W-30", 5.5, "örnek: 13mm / Torx", oil_filter_part="örnek: 31372212", air_filter_part="örnek: 31370161", cabin_filter_part="örnek: 31407811", spark_plug_part="örnek: Denso (benzin)", battery_spec="70-80Ah (AGM) / Recharge yüksek voltaj", battery_location="motor bölmesi / bagaj", transmission_type="otomatik / elektrikli")),
    car("Volvo", "S60", 2010, 2024, ["benzin", "dizel", "hibrit"], spec("0W-20 / 0W-30", 5.5, "örnek: 13mm / Torx", oil_filter_part="örnek: 31372212", air_filter_part="örnek: 31370161", cabin_filter_part="örnek: 31407811", spark_plug_part="örnek: Denso (benzin)", battery_spec="70-80Ah (AGM)", battery_location="motor bölmesi / bagaj", transmission_type="otomatik (Aisin 8AT)")),
    car("Land Rover", "Range Rover Evoque", 2011, 2024, ["benzin", "dizel", "hibrit"], spec("5W-30", 5.5, "örnek: Torx", oil_filter_part="örnek: LR025306", air_filter_part="örnek: LR029078", cabin_filter_part="örnek: LR036369", spark_plug_part="örnek: NGK (benzin)", battery_spec="80Ah (AGM)", battery_location="bagaj / motor bölmesi", transmission_type="otomatik (ZF 9HP)")),
    car("Tofaş", "Şahin", 1990, 2002, ["benzin", "lpg"], spec("15W-40 / 20W-50", 3.5, "14mm", oil_filter_part="örnek: klasik yağ filtresi", air_filter_part="örnek: klasik hava filtresi", cabin_filter_part=None, spark_plug_part="örnek: NGK BPR6ES (benzin)", battery_spec="45-55Ah", transmission_type="manuel")),
    car("Tofaş", "Doğan", 1990, 2002, ["benzin", "lpg"], spec("15W-40 / 20W-50", 3.5, "14mm", oil_filter_part="örnek: klasik yağ filtresi", air_filter_part="örnek: klasik hava filtresi", cabin_filter_part=None, spark_plug_part="örnek: NGK BPR6ES (benzin)", battery_spec="45-55Ah", transmission_type="manuel")),
]

existing = {(r["make"].casefold(), r["model"].casefold(), r["vehicle_type"]) for r in rows}
added, skipped = 0, []
for e in NEW:
    key = (e["make"].casefold(), e["model"].casefold(), e["vehicle_type"])
    if key in existing:
        skipped.append(f'{e["make"]} {e["model"]}')
        continue
    rows.append(e)
    existing.add(key)
    added += 1

DATA.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("eklendi:", added, "| atlandi(dup):", skipped, "| toplam:", len(rows))
