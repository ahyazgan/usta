"""Tek seferlik: TR pazarındaki yaygın MOTOSİKLETleri + eksik arabaları ekler.

Duplicate kontrollü ((make, model, vehicle_type)). Spec değerleri temel/örnek;
parça no'ları "örnek:" yer tutucu — el kitabına karşı doğrulanmalı. Motosiklette
kabin filtresi yoktur (cabin_filter_part=None). LPG müdahale tarifi YOK.
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


def moto(make, model, ymin, ymax, s, fuels=("benzin",), engine_codes=()):
    """Motosiklet kaydı: kabin filtresi None, tahliye konumu motor karteri."""
    s.setdefault("oil_drain_location", "motor karteri altı tahliye cıvatası")
    s["cabin_filter_part"] = None
    s["battery_location"] = s.get("battery_location_moto", "sele altı")
    s.pop("battery_location_moto", None)
    return {
        "make": make,
        "model": model,
        "year_min": int(ymin),
        "year_max": int(ymax),
        "vehicle_type": "motosiklet",
        "fuels": list(fuels),
        "engine_codes": list(engine_codes),
        "spec": s,
    }


def mspec(oil_spec, cap, bolt="14mm", plug=None, batt="12V 6-8Ah", trans="manuel"):
    """Kısa motosiklet spec yardımcısı (yaygın değerlerle)."""
    return spec(
        oil_spec=oil_spec,
        oil_capacity_l=cap,
        oil_drain_bolt_size=bolt,
        oil_drain_location="motor karteri altı tahliye cıvatası",
        oil_filter_part="örnek: elek tip / model-spesifik",
        air_filter_part="örnek: model-spesifik hava filtresi",
        spark_plug_part=plug or "örnek: NGK uygun",
        battery_spec=batt,
        transmission_type=trans,
    )


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


NEW = [
    # ===================== MOTOSİKLETLER (TR yaygın) =====================
    # --- Honda ---
    moto("Honda", "CB125F", 2015, 2024, mspec("10W-30", 1.1, "12mm", "örnek: NGK CPR6EA-9", "12V 3.5Ah (YTZ4V)")),
    moto("Honda", "CB125R", 2018, 2024, mspec("10W-30", 1.2, "12mm", "örnek: NGK CPR8EA-9", "12V")),
    moto("Honda", "CBF150", 2010, 2018, mspec("10W-30", 1.0, "12mm", "örnek: NGK CPR7EA-9", "12V 4Ah")),
    moto("Honda", "CBR250R", 2011, 2018, mspec("10W-30", 1.4, "12mm", "örnek: NGK SIMR8A9", "12V 6Ah")),
    moto("Honda", "Activa", 2012, 2024, mspec("10W-30", 0.8, "12mm", "örnek: NGK CPR6EA-9S", "12V 4Ah", "otomatik (CVT)")),
    moto("Honda", "Spacy", 2010, 2018, mspec("10W-30", 0.8, "12mm", "örnek: NGK CPR6EA-9", "12V 4Ah", "otomatik (CVT)")),
    moto("Honda", "Forza 250", 2018, 2024, mspec("10W-30", 1.7, "14mm", "örnek: NGK CPR8EA-9", "12V 8Ah", "otomatik (CVT)")),
    moto("Honda", "Africa Twin", 2016, 2024, mspec("10W-40 (JASO MA2)", 4.8, "14mm", "örnek: NGK CPR8EB-9", "12V 11Ah")),
    moto("Honda", "CB500F", 2013, 2024, mspec("10W-30 (JASO MA2)", 3.2, "14mm", "örnek: NGK CPR8EA-9", "12V 7Ah")),
    moto("Honda", "CB650R", 2019, 2024, mspec("10W-30 (JASO MA2)", 2.7, "14mm", "örnek: NGK CPR9EA-9", "12V 8Ah")),
    # --- Yamaha ---
    moto("Yamaha", "Crypton", 2008, 2024, mspec("10W-40 (JASO MA2)", 0.9, "17mm", "örnek: NGK CR6HSA", "12V 4Ah")),
    moto("Yamaha", "Cygnus", 2010, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR7HSA", "12V 6Ah", "otomatik (CVT)")),
    moto("Yamaha", "XMAX 250", 2014, 2024, mspec("10W-40 (JASO MA2)", 1.7, "14mm", "örnek: NGK CPR8EA-9", "12V 8Ah (YTZ8V)", "otomatik (CVT)")),
    moto("Yamaha", "XMAX 125", 2017, 2024, mspec("10W-40 (JASO MA2)", 1.1, "12mm", "örnek: NGK CPR8EA-9", "12V 6Ah", "otomatik (CVT)")),
    moto("Yamaha", "Tracer 700", 2016, 2024, mspec("10W-40 (JASO MA2)", 3.0, "14mm", "örnek: NGK LMAR8A-9", "12V 8Ah")),
    moto("Yamaha", "Tracer 900", 2015, 2024, mspec("10W-40 (JASO MA2)", 3.4, "14mm", "örnek: NGK CR9EK", "12V 8Ah")),
    moto("Yamaha", "MT-07", 2014, 2024, mspec("10W-40 (JASO MA2)", 3.0, "14mm", "örnek: NGK LMAR8A-9", "12V 8Ah")),
    moto("Yamaha", "MT-09", 2013, 2024, mspec("10W-40 (JASO MA2)", 3.4, "14mm", "örnek: NGK CR9EK", "12V 8Ah")),
    moto("Yamaha", "R25", 2014, 2024, mspec("10W-40 (JASO MA2)", 2.4, "14mm", "örnek: NGK CR9E", "12V (GTZ8V)")),
    # NOT: 2 zamanlı moped (PW50 vb.) eklenMEZ — yağ tahliyesi yoktur (yağ benzinle
    # karışır), oil_change rehberi onları yanlış yönlendirir (safety-auditor YÜKSEK).
    # --- Suzuki ---
    moto("Suzuki", "GSX-R150", 2017, 2024, mspec("10W-40 (JASO MA2)", 1.1, "12mm", "örnek: NGK CR8E", "12V 5Ah")),
    moto("Suzuki", "GSX-S150", 2017, 2024, mspec("10W-40 (JASO MA2)", 1.1, "12mm", "örnek: NGK CR8E", "12V 5Ah")),
    moto("Suzuki", "V-Strom 250", 2017, 2024, mspec("10W-40 (JASO MA2)", 1.6, "14mm", "örnek: NGK CR8E", "12V 7Ah")),
    moto("Suzuki", "Address 110", 2015, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR6HSA", "12V 4Ah", "otomatik (CVT)")),
    moto("Suzuki", "Burgman 400", 2017, 2024, mspec("10W-40 (JASO MA2)", 1.6, "14mm", "örnek: NGK CR7E", "12V 10Ah", "otomatik (CVT)")),
    # --- Kawasaki ---
    moto("Kawasaki", "Ninja 250", 2013, 2024, mspec("10W-40 (JASO MA2)", 1.7, "14mm", "örnek: NGK CR9EIA-9", "12V 6Ah")),
    moto("Kawasaki", "Ninja 400", 2018, 2024, mspec("10W-40 (JASO MA2)", 1.9, "14mm", "örnek: NGK CR9EIA-9", "12V 8Ah")),
    moto("Kawasaki", "Z250", 2013, 2024, mspec("10W-40 (JASO MA2)", 1.7, "14mm", "örnek: NGK CR9EIA-9", "12V 6Ah")),
    moto("Kawasaki", "Z900", 2017, 2024, mspec("10W-40 (JASO MA2)", 3.3, "14mm", "örnek: NGK CR9EIA-9", "12V 8Ah")),
    moto("Kawasaki", "Versys 650", 2010, 2024, mspec("10W-40 (JASO MA2)", 2.4, "14mm", "örnek: NGK CR9EIA-9", "12V 10Ah")),
    # --- KTM ---
    moto("KTM", "Duke 200", 2012, 2024, mspec("10W-50 (JASO MA2)", 1.3, "14mm", "örnek: NGK LKAR8A-9", "12V 8Ah")),
    moto("KTM", "Duke 390", 2013, 2024, mspec("10W-50 (JASO MA2)", 1.5, "14mm", "örnek: NGK LKAR8A-9", "12V 8Ah")),
    moto("KTM", "Adventure 390", 2020, 2024, mspec("10W-50 (JASO MA2)", 1.5, "14mm", "örnek: NGK LKAR8A-9", "12V 8Ah")),
    # --- İtalyan / Avrupa scooter & roadster ---
    moto("Vespa", "Primavera 125", 2014, 2024, mspec("5W-40 (JASO MA2)", 1.0, "12mm", "örnek: NGK CR8EB", "12V 7Ah", "otomatik (CVT)")),
    moto("Vespa", "GTS 300", 2010, 2024, mspec("5W-40 (JASO MA2)", 1.4, "14mm", "örnek: NGK CR8EB", "12V 10Ah", "otomatik (CVT)")),
    moto("Piaggio", "Liberty 125", 2010, 2024, mspec("5W-40 (JASO MA2)", 1.0, "12mm", "örnek: NGK CR8EB", "12V 7Ah", "otomatik (CVT)")),
    moto("Piaggio", "Medley 125", 2016, 2024, mspec("5W-40 (JASO MA2)", 1.1, "12mm", "örnek: NGK CR8EB", "12V 8Ah", "otomatik (CVT)")),
    moto("Benelli", "TRK 502", 2017, 2024, mspec("10W-40 (JASO MA2)", 3.0, "14mm", "örnek: NGK CR8E", "12V 10Ah")),
    moto("Benelli", "Leoncino 250", 2018, 2024, mspec("10W-40 (JASO MA2)", 1.5, "14mm", "örnek: NGK CR8E", "12V 7Ah")),
    moto("Aprilia", "SR 150", 2016, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR7HSA", "12V 5Ah", "otomatik (CVT)")),
    moto("BMW", "G 310 R", 2016, 2024, mspec("5W-40 (JASO MA2)", 1.5, "14mm", "örnek: NGK LMAR8A-9", "12V 8Ah")),
    moto("BMW", "F 750 GS", 2018, 2024, mspec("5W-40 (JASO MA2)", 3.0, "14mm", "örnek: NGK LMAR8A-9", "12V 12Ah")),
    moto("BMW", "R 1250 GS", 2019, 2024, mspec("5W-40 (JASO MA2)", 4.0, "14mm", "örnek: NGK MAR9A-J", "12V 12Ah")),
    moto("Husqvarna", "Svartpilen 250", 2020, 2024, mspec("10W-50 (JASO MA2)", 1.5, "14mm", "örnek: NGK LKAR8A-9", "12V 8Ah")),
    # --- Asya / TR pazarı uygun fiyat ---
    moto("SYM", "Symphony 125", 2010, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR7HSA", "12V 5Ah", "otomatik (CVT)")),
    moto("SYM", "Jet 14", 2018, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR7HSA", "12V 5Ah", "otomatik (CVT)")),
    moto("Kymco", "Agility 125", 2010, 2024, mspec("10W-40 (JASO MA2)", 0.9, "12mm", "örnek: NGK CR7HSA", "12V 5Ah", "otomatik (CVT)")),
    moto("Kymco", "People S 150", 2010, 2024, mspec("10W-40 (JASO MA2)", 1.0, "12mm", "örnek: NGK CR7HSA", "12V 6Ah", "otomatik (CVT)")),
    moto("CFMoto", "250 NK", 2018, 2024, mspec("10W-40 (JASO MA2)", 1.7, "14mm", "örnek: NGK CR8E", "12V 7Ah")),
    moto("CFMoto", "650 MT", 2018, 2024, mspec("10W-40 (JASO MA2)", 2.7, "14mm", "örnek: NGK CR8E", "12V 10Ah")),
    moto("Bajaj", "Dominar 400", 2017, 2024, mspec("10W-50 (JASO MA2)", 1.3, "14mm", "örnek: NGK CR8EK", "12V 8Ah")),
    moto("TVS", "Apache RTR 200", 2016, 2024, mspec("10W-40 (JASO MA2)", 1.1, "14mm", "örnek: NGK uygun", "12V 5Ah")),
    # --- TR yerli/uygun fiyat markalar ---
    moto("Mondial", "Drift 125", 2015, 2024, mspec("10W-40 (JASO MA2)", 1.0, "17mm", "örnek: NGK C7HSA", "12V 4Ah")),
    moto("Mondial", "150 MG", 2012, 2024, mspec("10W-40 (JASO MA2)", 1.1, "17mm", "örnek: NGK C7HSA", "12V 5Ah")),
    moto("Arora", "Cappadocia 250", 2015, 2024, mspec("10W-40 (JASO MA2)", 1.5, "14mm", "örnek: NGK uygun", "12V 7Ah")),
    moto("Arora", "AR 125", 2012, 2024, mspec("10W-40 (JASO MA2)", 1.0, "17mm", "örnek: NGK C7HSA", "12V 4Ah")),
    moto("Falcon", "Sertao 250", 2014, 2024, mspec("10W-40 (JASO MA2)", 1.5, "14mm", "örnek: NGK uygun", "12V 7Ah")),
    moto("Daelim", "Daystar 125", 2010, 2022, mspec("10W-40 (JASO MA2)", 1.1, "17mm", "örnek: NGK CR7HSA", "12V 5Ah")),
    moto("Bisan", "Moped 50", 2010, 2024, mspec("10W-40 (JASO MA2)", 0.8, "17mm", "örnek: NGK C7HSA", "12V 4Ah")),
    moto("Yuki", "YK 125", 2012, 2024, mspec("10W-40 (JASO MA2)", 1.0, "17mm", "örnek: NGK C7HSA", "12V 4Ah")),

    # ===================== EKSİK ARABALAR (TR yaygın) =====================
    car("Renault", "Megane Sedan", 2016, 2024, ["benzin", "dizel"], spec("5W-30", 4.8, "8mm iç altıgen (allen)", oil_filter_part="örnek: 8200768927", air_filter_part="örnek: 165461376R", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah", battery_location="motor bölmesi sağ ön", transmission_type="manuel / EDC")),
    car("Renault", "Latitude", 2011, 2016, ["benzin", "dizel"], spec("5W-40", 5.4, "8mm iç altıgen (allen)", oil_filter_part="örnek: 8200768927", air_filter_part="örnek: 8200431051", cabin_filter_part="örnek: 272773016R", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah", battery_location="motor bölmesi sağ ön", transmission_type="otomatik")),
    car("Fiat", "Egea Cross", 2020, 2024, ["benzin", "dizel"], spec("5W-40", 3.0, "14mm", oil_filter_part="örnek: 55256470", air_filter_part="örnek: 51897064", cabin_filter_part="örnek: 77367464", spark_plug_part="örnek: NGK DCPR7E-N-10 (benzin)", battery_spec="60Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / otomatik")),
    car("Fiat", "Fiorino", 2008, 2024, ["dizel", "benzin"], spec("5W-40", 3.8, "14mm", oil_filter_part="örnek: 55256470", air_filter_part="örnek: 51897064", cabin_filter_part="örnek: 77367464", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel")),
    car("Opel", "Astra", 2021, 2024, ["benzin", "hibrit"], spec("5W-30", 4.0, "örnek: Torx / 13mm", oil_filter_part="örnek: 9808867680", air_filter_part="örnek: 9809282680", cabin_filter_part="örnek: 9808158480", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah (EFB)", battery_location="motor bölmesi sol ön", transmission_type="manuel / otomatik")),
    car("Volkswagen", "Polo", 2022, 2024, ["benzin"], spec("5W-30 (VW 504.00)", 3.6, "19mm", oil_filter_part="örnek: 04E115561H", air_filter_part="örnek: 2Q0129620", cabin_filter_part="örnek: 2Q0819653", spark_plug_part="örnek: NGK 04E905602D (benzin)", battery_spec="60Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Toyota", "Corolla Cross", 2021, 2024, ["benzin", "hibrit"], spec("0W-16 / 0W-20", 4.2, "14mm", oil_filter_part="örnek: 04152-YZZA6", air_filter_part="örnek: 17801-25020", cabin_filter_part="örnek: 87139-0N010", spark_plug_part="örnek: Denso (benzin)", battery_spec="45-60Ah / hibrit yardımcı", battery_location="motor bölmesi / bagaj (hibrit)", transmission_type="e-CVT (hibrit) / CVT")),
    car("Toyota", "Camry", 2018, 2024, ["benzin", "hibrit"], spec("0W-16 / 0W-20", 4.8, "14mm", oil_filter_part="örnek: 04152-YZZA6", air_filter_part="örnek: 17801-0H080", cabin_filter_part="örnek: 87139-06040", spark_plug_part="örnek: Denso (benzin)", battery_spec="45-60Ah / hibrit yardımcı", battery_location="motor bölmesi / bagaj (hibrit)", transmission_type="e-CVT (hibrit) / otomatik")),
    car("Hyundai", "i10", 2014, 2024, ["benzin", "lpg"], spec("5W-30", 3.3, "17mm", oil_filter_part="örnek: 26300-02503", air_filter_part="örnek: 28113-B9000", cabin_filter_part="örnek: 97133-1J000", spark_plug_part="örnek: NGK (benzin)", battery_spec="45Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / otomatik")),
    car("Kia", "Picanto", 2011, 2024, ["benzin", "lpg"], spec("5W-30", 3.3, "17mm", oil_filter_part="örnek: 26300-02503", air_filter_part="örnek: 28113-1Y100", cabin_filter_part="örnek: 97133-1Y000", spark_plug_part="örnek: NGK (benzin)", battery_spec="45Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / otomatik")),
    car("Nissan", "Note", 2013, 2021, ["benzin"], spec("5W-30 / 5W-40", 3.4, "14mm", oil_filter_part="örnek: 15208-65F0E", air_filter_part="örnek: 16546-1HK0A", cabin_filter_part="örnek: 27277-1HB0A", spark_plug_part="örnek: NGK (benzin)", battery_spec="45-55Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / CVT")),
    car("Peugeot", "Partner", 2010, 2024, ["dizel", "benzin"], spec("5W-30", 4.25, "örnek: Torx / 13mm", oil_filter_part="örnek: 1109AY", air_filter_part="örnek: 1444TT", cabin_filter_part="örnek: 6447XF", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / EAT8")),
    car("Citroen", "C-Elysee", 2023, 2024, ["benzin"], spec("5W-30", 3.25, "13mm iç altıgen (allen)", oil_filter_part="örnek: 1109AY", air_filter_part="örnek: 1444TT", cabin_filter_part="örnek: 6447XF", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah", battery_location="motor bölmesi sol ön", transmission_type="manuel / otomatik")),
    car("Skoda", "Scala", 2019, 2024, ["benzin"], spec("5W-30 (VW 504.00)", 4.0, "19mm", oil_filter_part="örnek: 04E115561H", air_filter_part="örnek: 2Q0129620", cabin_filter_part="örnek: 5Q0819669", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Seat", "Arona", 2017, 2024, ["benzin"], spec("5W-30 (VW 504.00)", 4.0, "19mm", oil_filter_part="örnek: 04E115561H", air_filter_part="örnek: 2Q0129620", cabin_filter_part="örnek: 5Q0819669", spark_plug_part="örnek: NGK (benzin)", battery_spec="60Ah (EFB)", battery_location="motor bölmesi sol arka", transmission_type="manuel / DSG")),
    car("Mercedes-Benz", "CLA", 2013, 2024, ["benzin", "dizel"], spec("5W-30 (MB 229.51)", 5.5, "13mm", oil_filter_part="örnek: A2701800109", air_filter_part="örnek: A2700940204", cabin_filter_part="örnek: A2468300018", spark_plug_part="örnek: NGK (benzin)", battery_spec="60-70Ah (AGM)", battery_location="motor bölmesi", transmission_type="otomatik (7G-DCT)")),
    car("BMW", "X2", 2018, 2024, ["benzin", "dizel"], spec("5W-30 (BMW LL-04)", 5.0, "8mm iç altıgen (allen)", oil_filter_part="örnek: 11428583898", air_filter_part="örnek: 13718580427", cabin_filter_part="örnek: 64319321046", spark_plug_part="örnek: NGK (benzin)", battery_spec="70Ah (AGM)", battery_location="bagaj / motor bölmesi", transmission_type="otomatik")),
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
