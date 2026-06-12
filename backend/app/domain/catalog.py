"""TR araç parkı bakım kataloğu (seed/örnek veri).

Türkiye'de yaygın araçlar için yağ/filtre/akü gibi bakım verilerini tutar.
Araç oluştururken kullanıcı `spec` vermezse buradan otomatik doldurulur.

⚠️ Veriler KARIŞIK güvendedir:
- Bazı specler (yağ vizkozitesi/kapasite, buji tipi, akü) en çok satan modeller
  için web kaynaklarından doğrulandı — "örnek:" ön eki YOK.
- "örnek:" ön ekli değerler (özellikle filtre OE parça no'ları) hâlâ YER TUTUCU;
  üretimde araç el kitabına / yetkili parça kataloğuna karşı doğrulanmalı.
NOT: Tek-girdi-per-model yapısı motor varyantını (yıl/facelift) tam yakalayamaz;
gerçek OE parça uyumluluğu için harici parça verisi (perakendeci/TecDoc) gerekir.
AI rehberliği bu verileri "kesin" değil referans olarak kullanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import FuelType, VehicleType
from .schemas import VehicleSpecIn


@dataclass(slots=True, frozen=True)
class CatalogEntry:
    make: str
    model: str
    year_min: int
    year_max: int
    spec: VehicleSpecIn
    fuels: tuple[FuelType, ...] = field(default=())
    engine_codes: tuple[str, ...] = field(default=())
    vehicle_type: VehicleType = VehicleType.araba


# Not: LPG'li benzinli araçlarda LPG sistemine müdahale TARİFİ verilmez;
# katalog yalnızca temel bakım verisini taşır.
CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        make="Fiat",
        model="Egea",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("843A1000",),  # 1.4 Fire 95hp
        spec=VehicleSpecIn(
            # 1.4 Fire (843A1000): yağ ~3.0L, buji NGK DCPR7E-N-10 (web-doğrulandı).
            oil_spec="5W-40",
            oil_capacity_l=3.0,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt-arka köşe",
            oil_filter_part="örnek: 55256470",
            air_filter_part="örnek: 51897064",
            cabin_filter_part="örnek: 77367464",
            spark_plug_part="NGK DCPR7E-N-10",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Fiat",
        model="Egea",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.dizel,),
        engine_codes=("198A2000", "199B1000"),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=4.3,
            oil_drain_bolt_size="13mm",
            oil_drain_location="yağ karteri alt-arka",
            oil_filter_part="örnek: 71754237",
            air_filter_part="örnek: 51897064",
            cabin_filter_part="örnek: 77367464",
            spark_plug_part=None,  # dizel — buji yok
            battery_spec="70Ah / 630A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Clio",
        year_min=2012,
        year_max=2023,
        fuels=(FuelType.dizel,),
        engine_codes=("K9K",),
        spec=VehicleSpecIn(
            # 1.5 dCi K9K: yağ 5W-30 ~4.8L (web-doğrulandı). Dizel → buji yok.
            oil_spec="5W-30",
            oil_capacity_l=4.8,
            oil_drain_bolt_size="8mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 8200768927",
            air_filter_part="örnek: 165466455R",
            cabin_filter_part="örnek: 272773016R",
            spark_plug_part=None,
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Megane",
        year_min=2016,
        year_max=2023,
        fuels=(FuelType.dizel,),
        engine_codes=("K9K",),
        spec=VehicleSpecIn(
            # 1.5 dCi K9K (Clio ile aynı motor): yağ 5W-30 ~4.8L (web-doğrulandı).
            oil_spec="5W-30",
            oil_capacity_l=4.8,
            oil_drain_bolt_size="8mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 8200768927",
            air_filter_part="örnek: 165461376R",
            cabin_filter_part="örnek: 272773016R",
            spark_plug_part=None,
            battery_spec="70Ah / 630A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Toyota",
        model="Corolla",
        year_min=2013,
        year_max=2019,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("1ZR-FAE",),
        spec=VehicleSpecIn(
            # 1ZR-FAE: yağ 0W-20 ~4.2L, buji NGK ILKAR7B-11 / Denso SC16HR11 (web-doğrulandı).
            oil_spec="0W-20",
            oil_capacity_l=4.2,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 04152-YZZA1",
            air_filter_part="örnek: 17801-0T050",
            cabin_filter_part="örnek: 87139-0N010",
            spark_plug_part="NGK ILKAR7B-11 (Denso SC16HR11)",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Dacia",
        model="Sandero",
        year_min=2013,
        year_max=2020,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("H4B", "B4D"),
        spec=VehicleSpecIn(
            # Yağ kapasitesi motora bağlı: 1.0 SCe ~3.0L, TCe ~4.4L — varyant farkı.
            oil_spec="5W-30",
            oil_capacity_l=4.0,
            oil_drain_bolt_size="10mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 152089599R",
            air_filter_part="örnek: 165465154R",
            cabin_filter_part="örnek: 272772835R",
            spark_plug_part="örnek: NGK LZKAR6AP-11",
            battery_spec="50-58Ah",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Volkswagen",
        model="Golf",
        year_min=2013,
        year_max=2020,
        fuels=(FuelType.benzin, FuelType.dizel),
        engine_codes=("CJZ", "CUU", "DGT"),
        spec=VehicleSpecIn(
            # 1.4 TSI EA211: yağ VW 504.00 ~4.0L, buji OE 04E905602D (web-doğrulandı).
            oil_spec="5W-30 (VW 504.00)",
            oil_capacity_l=4.0,
            oil_drain_bolt_size="19mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 04E115561H",
            air_filter_part="örnek: 5Q0129620D",
            cabin_filter_part="örnek: 5Q0819669",
            spark_plug_part="NGK 04E905602D (IKER7A8EGS)",
            battery_spec="60Ah / 640A (EFB)",
            battery_location="motor bölmesi sol arka",
            transmission_type="manuel / DSG",
        ),
    ),
    CatalogEntry(
        make="Volkswagen",
        model="Polo",
        year_min=2010,
        year_max=2021,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=3.6,
            oil_drain_bolt_size="19mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 03C115561H",
            air_filter_part="örnek: 6R0129620",
            cabin_filter_part="örnek: 6R0819653",
            spark_plug_part="örnek: NGK 03C905600B",
            battery_spec="51Ah / 470A",
            battery_location="motor bölmesi sol arka",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Hyundai",
        model="i20",
        year_min=2014,
        year_max=2023,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            # 1.4 MPI Gamma: yağ 5W-30 ~3.3L (web-doğrulandı).
            oil_spec="5W-30",
            oil_capacity_l=3.3,
            oil_drain_bolt_size="17mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 26300-35505",
            air_filter_part="örnek: 28113-1J000",
            cabin_filter_part="örnek: 97133-1J000",
            spark_plug_part="örnek: NGK SILZKR6B-10E",
            battery_spec="55Ah / 480A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Ford",
        model="Focus",
        year_min=2011,
        year_max=2018,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=4.1,
            oil_drain_bolt_size="13mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 1751529",
            air_filter_part="örnek: 1848220",
            cabin_filter_part="örnek: 1812519",
            spark_plug_part="örnek: NGK ITR6F13 (benzin)",
            battery_spec="60Ah / 590A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel / Powershift",
        ),
    ),
    CatalogEntry(
        make="Opel",
        model="Astra",
        year_min=2010,
        year_max=2021,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30 (dexos2)",
            oil_capacity_l=4.5,
            oil_drain_bolt_size="15mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 55594651",
            air_filter_part="örnek: 13272719",
            cabin_filter_part="örnek: 13271190",
            spark_plug_part="örnek: ACDelco / NGK uygun",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Peugeot",
        model="301",
        year_min=2012,
        year_max=2022,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=3.7,
            oil_drain_bolt_size="13mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 1109AY",
            air_filter_part="örnek: 1444TT",
            cabin_filter_part="örnek: 6447XF",
            spark_plug_part="örnek: NGK uygun (benzin)",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Honda",
        model="Civic",
        year_min=2012,
        year_max=2021,
        fuels=(FuelType.benzin,),
        spec=VehicleSpecIn(
            oil_spec="0W-20 / 5W-30",
            oil_capacity_l=3.7,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 15400-PLM-A02",
            air_filter_part="örnek: 17220-5BA-A00",
            cabin_filter_part="örnek: 80292-TBA-A11",
            spark_plug_part="örnek: NGK DILKAR7G11GS",
            battery_spec="45Ah / 400A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel / CVT",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Clio",
        year_min=2013,
        year_max=2023,
        fuels=(FuelType.benzin, FuelType.lpg),
        engine_codes=("H4B", "H5H"),
        spec=VehicleSpecIn(
            oil_spec="5W-40",
            oil_capacity_l=4.2,
            oil_drain_bolt_size="10mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 152089599R",
            air_filter_part="örnek: 165466455R",
            cabin_filter_part="örnek: 272773016R",
            spark_plug_part="örnek: NGK LZKAR6AP-11",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Renault",
        model="Symbol",
        year_min=2013,
        year_max=2022,
        fuels=(FuelType.benzin, FuelType.lpg),
        spec=VehicleSpecIn(
            oil_spec="5W-40",
            oil_capacity_l=4.2,
            oil_drain_bolt_size="10mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 152089599R",
            air_filter_part="örnek: 165465154R",
            cabin_filter_part="örnek: 272772835R",
            spark_plug_part="örnek: NGK LZKAR6AP-11",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sağ ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Hyundai",
        model="Accent Blue",
        year_min=2011,
        year_max=2019,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=3.6,
            oil_drain_bolt_size="17mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 26300-35504",
            air_filter_part="örnek: 28113-1R100",
            cabin_filter_part="örnek: 97133-2H000",
            spark_plug_part="örnek: NGK SILZKR6B-10E",
            battery_spec="55Ah / 480A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Nissan",
        model="Qashqai",
        year_min=2014,
        year_max=2021,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-40",
            oil_capacity_l=4.6,
            oil_drain_bolt_size="14mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 15208-65F0E",
            air_filter_part="örnek: 16546-4BA1A",
            cabin_filter_part="örnek: 27277-4BA0A",
            spark_plug_part="örnek: NGK DILKAR7E11 (benzin)",
            battery_spec="65Ah / 580A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel / Xtronic CVT",
        ),
    ),
    CatalogEntry(
        make="Skoda",
        model="Octavia",
        year_min=2013,
        year_max=2020,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30 (VW 504.00)",
            oil_capacity_l=4.3,
            oil_drain_bolt_size="19mm",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 04E115561H",
            air_filter_part="örnek: 5Q0129620D",
            cabin_filter_part="örnek: 5Q0819669",
            spark_plug_part="örnek: NGK 04E905612",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol arka",
            transmission_type="manuel / DSG",
        ),
    ),
    CatalogEntry(
        make="Citroen",
        model="C-Elysee",
        year_min=2013,
        year_max=2022,
        fuels=(FuelType.benzin, FuelType.dizel),
        spec=VehicleSpecIn(
            oil_spec="5W-30",
            oil_capacity_l=3.7,
            oil_drain_bolt_size="13mm iç altıgen (allen)",
            oil_drain_location="yağ karteri alt orta",
            oil_filter_part="örnek: 1109AY",
            air_filter_part="örnek: 1444TT",
            cabin_filter_part="örnek: 6447XF",
            spark_plug_part="örnek: NGK uygun (benzin)",
            battery_spec="60Ah / 540A",
            battery_location="motor bölmesi sol ön",
            transmission_type="manuel",
        ),
    ),
    # --- MOTOSİKLETLER (TR'de yaygın; değerler ÖRNEK, el kitabına karşı doğrula) ---
    CatalogEntry(
        make="Honda",
        model="CB125",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        engine_codes=("JC64",),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-30",
            oil_capacity_l=1.1,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip / 15412-KGA-900",
            air_filter_part="örnek: 17211-K0G-900",
            cabin_filter_part=None,  # motosiklette kabin filtresi yok
            spark_plug_part="örnek: NGK CPR6EA-9",
            battery_spec="12V 3.5Ah (YTZ4V)",
            battery_location="sele altı",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Yamaha",
        model="YBR125",
        year_min=2008,
        year_max=2022,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40",
            oil_capacity_l=1.0,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: 3D9-E4450-00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CR6HSA",
            battery_spec="12V 5Ah (YB5L-B)",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Honda",
        model="PCX125",
        year_min=2014,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-30",
            oil_capacity_l=0.8,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip",
            air_filter_part="örnek: 17210-K35-V00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR7EA-9",
            battery_spec="12V (GTZ6V)",
            battery_location="ayak tabanı / sele altı",
            transmission_type="otomatik (CVT)",
        ),
    ),
    CatalogEntry(
        make="Yamaha",
        model="MT-25",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40",
            oil_capacity_l=2.4,
            oil_drain_bolt_size="14mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: 1WD-E3440-00",
            air_filter_part="örnek: 1WD-14451-00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR8EA-9",
            battery_spec="12V 7Ah (YTZ7S)",
            battery_location="sele altı",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Mondial",
        model="125",
        year_min=2010,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40 (motosiklet, JASO MA2)",
            oil_capacity_l=1.0,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: model-spesifik sünger/kağıt",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CR7HSA / C7HSA",
            battery_spec="12V 4-5Ah",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Kuba",
        model="125",
        year_min=2008,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40 (motosiklet, JASO MA2)",
            oil_capacity_l=0.9,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: model-spesifik sünger/kağıt",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK C7HSA",
            battery_spec="12V 4Ah",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="RKS",
        model="125",
        year_min=2010,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40 (motosiklet, JASO MA2)",
            oil_capacity_l=1.0,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: model-spesifik sünger/kağıt",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK C7HSA / CR7HSA",
            battery_spec="12V 4-5Ah",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Bajaj",
        model="Boxer",
        year_min=2014,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="20W-40 / 10W-40 (motosiklet)",
            oil_capacity_l=1.0,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: Bajaj OE hava filtresi",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CR8EH-9 / Bosch UR4AC",
            battery_spec="12V 5-9Ah",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Yamaha",
        model="NMAX",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-40 (motosiklet, JASO MA2)",
            oil_capacity_l=0.9,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip / B74-E3440-00",
            air_filter_part="örnek: B74-E4451-00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR8EA-9",
            battery_spec="12V (GTZ6V)",
            battery_location="ayak tabanı / sele altı",
            transmission_type="otomatik (CVT)",
        ),
    ),
    CatalogEntry(
        make="Honda",
        model="PCX150",
        year_min=2015,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-30 (motosiklet)",
            oil_capacity_l=0.9,
            oil_drain_bolt_size="12mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip",
            air_filter_part="örnek: 17210-K35-V00",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CPR7EA-9",
            battery_spec="12V (GTZ8V)",
            battery_location="ayak tabanı / sele altı",
            transmission_type="otomatik (CVT)",
        ),
    ),
    CatalogEntry(
        make="KTM",
        model="Duke 125",
        year_min=2017,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="10W-50 (motosiklet, JASO MA2)",
            oil_capacity_l=1.3,
            oil_drain_bolt_size="14mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: 90138015000",
            air_filter_part="örnek: 90106110000",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK LKAR8A-9",
            battery_spec="12V 8Ah",
            battery_location="sele altı",
            transmission_type="manuel",
        ),
    ),
    CatalogEntry(
        make="Bajaj",
        model="Pulsar",
        year_min=2012,
        year_max=2024,
        fuels=(FuelType.benzin,),
        vehicle_type=VehicleType.motosiklet,
        spec=VehicleSpecIn(
            oil_spec="20W-50 / 15W-40 (motosiklet)",
            oil_capacity_l=1.2,
            oil_drain_bolt_size="17mm",
            oil_drain_location="motor karteri altı tahliye cıvatası",
            oil_filter_part="örnek: elek tip (yıkanabilir)",
            air_filter_part="örnek: Bajaj OE hava filtresi",
            cabin_filter_part=None,
            spark_plug_part="örnek: NGK CR8EK / Bosch UR5DC",
            battery_spec="12V 8-9Ah",
            battery_location="sele altı / yan kapak",
            transmission_type="manuel",
        ),
    ),
)


def find_spec(
    make: str,
    model: str,
    year: int,
    *,
    fuel_type: FuelType | None = None,
    engine_code: str | None = None,
    vehicle_type: VehicleType | None = None,
) -> VehicleSpecIn | None:
    """Katalogda eşleşen aracın spec'ini döndürür; yoksa None.

    Eşleşme önceliği: motor kodu > yakıt türü > yıl aralığı.
    vehicle_type verilirse (None=eski çağrı) yalnızca o türdeki kayıtlar dikkate
    alınır (araba/motosiklet karışmasını önler).
    """
    make_n, model_n = make.strip().casefold(), model.strip().casefold()
    engine_n = engine_code.strip().casefold() if engine_code else None
    vtype = vehicle_type or VehicleType.araba

    candidates = [
        e
        for e in CATALOG
        if e.make.casefold() == make_n
        and e.model.casefold() == model_n
        and e.year_min <= year <= e.year_max
        and e.vehicle_type == vtype
    ]
    if not candidates:
        return None

    # Motor koduyla daralt.
    if engine_n:
        by_engine = [e for e in candidates if any(c.casefold() == engine_n for c in e.engine_codes)]
        if by_engine:
            candidates = by_engine

    # Yakıt türüyle daralt.
    if fuel_type is not None:
        by_fuel = [e for e in candidates if not e.fuels or fuel_type in e.fuels]
        if by_fuel:
            candidates = by_fuel

    return candidates[0].spec.model_copy(deep=True)
