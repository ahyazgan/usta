"""Adım adım bakım rehberleri.

Her görev için yapılandırılmış adımlar: talimat (TR/EN), gerekli alet, tork ve
adım-bazlı güvenlik uyarısı. Talimatlardaki `{anahtar}` yer tutucuları aracın
spec'inden doldurulur (örn. `{oil_drain_bolt_size}` → "14mm"); spec yoksa
dile uygun genel ifadeye düşer.

GÜVENLİK KURALLARI (EN YÜKSEK ÖNCELİK — bkz. domain/safety.py):
- Güvenlik-kritik görevlerde (fren, soğutma) rehber YALNIZCA gözlem adımları
  içerir; onarım/söküm tarifi verilmez.
- Sıcak motor / kriko / akü / yakıt / LPG bağlamlarında adım uyarısı zorunlu.
- Her rehberde "vazgeç, tamirciye git" çıkışı vardır (mechanic_note).
- LPG sistemine müdahale tarifi YASAK (rehberler LPG bileşenlerine dokunmaz).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Spec anahtarı -> dil bazlı genel ifade (spec'te değer yoksa).
_FALLBACKS_TR = {
    "oil_spec": "araca uygun yağ",
    "oil_capacity_l": "el kitabındaki kadar",
    "oil_drain_bolt_size": "uygun ölçüde",
    "oil_filter_part": "araca uygun yağ filtresi",
    "air_filter_part": "araca uygun hava filtresi",
    "cabin_filter_part": "araca uygun polen filtresi",
    "spark_plug_part": "araca uygun buji",
    "battery_spec": "araca uygun akü",
    "battery_location": "motor bölmesi",
}
_FALLBACKS_EN = {
    "oil_spec": "the oil your manual specifies",
    "oil_capacity_l": "the amount in your manual",
    "oil_drain_bolt_size": "the correct size",
    "oil_filter_part": "the right oil filter",
    "air_filter_part": "the right air filter",
    "cabin_filter_part": "the right cabin filter",
    "spark_plug_part": "the right spark plugs",
    "battery_spec": "the right battery",
    "battery_location": "the engine bay",
}


@dataclass(slots=True, frozen=True)
class GuideStep:
    instruction_tr: str
    instruction_en: str
    tool_tr: str | None = None
    tool_en: str | None = None
    torque_nm: int | None = None
    warning_tr: str | None = None
    warning_en: str | None = None


@dataclass(slots=True, frozen=True)
class TaskGuide:
    task_id: str
    est_minutes: int
    steps: tuple[GuideStep, ...] = field(default=())
    # Her rehberde zorunlu "vazgeç, tamirciye git" çıkışı.
    mechanic_note_tr: str = (
        "Emin değilsen veya bir terslik görürsen işlemi bırak ve tamirciye git."
    )
    mechanic_note_en: str = (
        "If you're unsure or something looks wrong, stop and see a mechanic."
    )


GUIDES: dict[str, TaskGuide] = {
    "oil_change": TaskGuide(
        task_id="oil_change",
        est_minutes=45,
        steps=(
            GuideStep(
                instruction_tr="Aracı düz zemine al, el frenini çek. Motor ılık olsun — sıcak DEĞİL. En az 30 dk soğumasını bekle.",
                instruction_en="Park on level ground and set the handbrake. Engine should be lukewarm — NOT hot. Wait at least 30 minutes.",
                warning_tr="Sıcak yağ ciddi yanığa yol açar. Motor sıcakken tıpayı açma.",
                warning_en="Hot oil causes serious burns. Never open the drain plug on a hot engine.",
            ),
            GuideStep(
                instruction_tr="Malzemeleri hazırla: yeni yağ ({oil_spec}, yaklaşık {oil_capacity_l} L), yağ filtresi ({oil_filter_part}), boş kap, eldiven.",
                instruction_en="Gather supplies: fresh oil ({oil_spec}, about {oil_capacity_l} L), an oil filter ({oil_filter_part}), a drain pan, gloves.",
                tool_tr="Filtre anahtarı, eldiven",
                tool_en="Filter wrench, gloves",
            ),
            GuideStep(
                instruction_tr="Tıpanın altına kabı yerleştir. {oil_drain_bolt_size} lokma anahtarıyla tahliye tıpasını saat yönünün tersine çevirip sök.",
                instruction_en="Place the pan under the plug. Loosen the drain plug counter-clockwise with a {oil_drain_bolt_size} socket.",
                tool_tr="{oil_drain_bolt_size} lokma anahtarı",
                tool_en="{oil_drain_bolt_size} socket wrench",
                warning_tr="Araç krikoyla kaldırıldıysa mutlaka takozla destekle; sadece kriko üzerindeyken altına girme.",
                warning_en="If the car is jacked up, always use stands; never go under a car held only by a jack.",
            ),
            GuideStep(
                instruction_tr="Yağın tamamen boşalmasını bekle (~10 dk). Bu sırada eski filtreyi filtre anahtarıyla sök.",
                instruction_en="Let the oil drain fully (~10 min). Meanwhile remove the old filter with the filter wrench.",
                tool_tr="Filtre anahtarı",
                tool_en="Filter wrench",
            ),
            GuideStep(
                instruction_tr="Yeni filtrenin contasına parmağınla ince bir kat temiz yağ sür ve filtreyi ELLE sık — anahtar kullanma.",
                instruction_en="Smear a thin film of clean oil on the new filter's gasket and tighten the filter by HAND — no wrench.",
            ),
            GuideStep(
                instruction_tr="Tıpayı (mümkünse yeni contayla) elle başlat, sonra yaklaşık 30 Nm ile sık. Aşırı sıkma — karter dişini bozar.",
                instruction_en="Start the plug by hand (new washer if possible), then tighten to roughly 30 Nm. Don't overtighten — you can strip the pan.",
                tool_tr="{oil_drain_bolt_size} lokma + tork anahtarı",
                tool_en="{oil_drain_bolt_size} socket + torque wrench",
                torque_nm=30,
            ),
            GuideStep(
                instruction_tr="Yeni yağı doldur (yaklaşık {oil_capacity_l} L), 1 dk çalıştır, durdur ve 2 dk sonra çubukla seviyeyi + tıpa/filtre çevresinde sızıntıyı kontrol et.",
                instruction_en="Fill with fresh oil (about {oil_capacity_l} L), run for 1 minute, stop, wait 2 minutes, then check the dipstick level and look for leaks at the plug/filter.",
                warning_tr="Motor çalıştıktan sonra egzoz manifoldu sıcaktır; sızıntı kontrolünde sıcak yüzeylere değme.",
                warning_en="After running, the exhaust manifold is hot; avoid touching hot surfaces while checking for leaks.",
            ),
        ),
    ),
    "air_filter": TaskGuide(
        task_id="air_filter",
        est_minutes=10,
        steps=(
            GuideStep(
                instruction_tr="Kontak kapalıyken motor bölmesindeki hava filtresi kutusunu bul (genelde plastik, körüklü boruya bağlı).",
                instruction_en="With the ignition off, find the air filter box in the engine bay (usually plastic, connected to a ribbed intake hose).",
            ),
            GuideStep(
                instruction_tr="Kutunun klipslerini aç (bazı modellerde birkaç vida olabilir) ve kapağı kaldır.",
                instruction_en="Release the box clips (some models also have a few screws) and lift the lid.",
                tool_tr="Gerekirse yıldız tornavida",
                tool_en="Phillips screwdriver if needed",
            ),
            GuideStep(
                instruction_tr="Eski filtreyi çıkar; yenisini ({air_filter_part}) aynı yönde yerleştir. Kutu içini kuru bezle sil.",
                instruction_en="Remove the old filter; seat the new one ({air_filter_part}) the same way. Wipe the box clean with a dry cloth.",
            ),
            GuideStep(
                instruction_tr="Kapağı kapat, klipsleri/vidaları tak. Boru bağlantısının tam oturduğundan emin ol.",
                instruction_en="Close the lid and refit clips/screws. Make sure the intake hose is fully seated.",
            ),
        ),
    ),
    "cabin_filter": TaskGuide(
        task_id="cabin_filter",
        est_minutes=15,
        steps=(
            GuideStep(
                instruction_tr="Polen filtresi çoğu araçta torpido arkasındadır. Torpidoyu boşalt ve yan sınırlayıcılarını içeri bastırarak aşağı serbest bırak.",
                instruction_en="The cabin filter usually sits behind the glovebox. Empty the glovebox and release its side stops by pressing them inward.",
            ),
            GuideStep(
                instruction_tr="Filtre kapağının klipsini açıp kapağı çıkar.",
                instruction_en="Unclip the filter cover and remove it.",
            ),
            GuideStep(
                instruction_tr="Eski filtreyi çekerek çıkar; hava akış yönü okuna dikkat ederek yenisini ({cabin_filter_part}) tak.",
                instruction_en="Slide the old filter out; insert the new one ({cabin_filter_part}) minding the airflow arrow.",
            ),
            GuideStep(
                instruction_tr="Kapağı ve torpidoyu geri tak. Fanı çalıştırıp hava akışını kontrol et.",
                instruction_en="Refit the cover and glovebox. Run the fan and check airflow.",
            ),
        ),
    ),
    "battery": TaskGuide(
        task_id="battery",
        est_minutes=10,
        steps=(
            GuideStep(
                instruction_tr="Kontağı kapat. Metal takıları (yüzük, saat, kolye) çıkar. Akü {battery_location} bölgesindedir.",
                instruction_en="Turn the ignition off. Remove metal jewellery (rings, watch, necklace). The battery is at {battery_location}.",
                warning_tr="Akü patlayıcı gaz çıkarır: sigara, alev ve kıvılcım kesinlikle yasak.",
                warning_en="Batteries vent explosive gas: no smoking, flames or sparks.",
            ),
            GuideStep(
                instruction_tr="Kutup başlarını GÖZLE kontrol et: beyaz/yeşil oksitlenme, gevşeklik veya çatlak var mı? ({battery_spec})",
                instruction_en="VISUALLY inspect the terminals: white/green corrosion, looseness or cracks? ({battery_spec})",
            ),
            GuideStep(
                instruction_tr="Gövdede şişme, çatlak veya sızıntı izi ara. Varsa aküye dokunma — doğrudan tamirciye git.",
                instruction_en="Look for swelling, cracks or leak marks on the case. If present, don't touch the battery — go straight to a mechanic.",
                warning_tr="Akü asidi cilde ve göze ciddi zarar verir.",
                warning_en="Battery acid causes serious skin and eye injury.",
            ),
            GuideStep(
                instruction_tr="Hafif oksitlenme varsa kutup temizliği ve sökme/takma işini tamirciye bırak; bu rehber yalnızca kontrol içindir.",
                instruction_en="If there's light corrosion, leave cleaning and removal/refitting to a mechanic; this guide is inspection-only.",
            ),
        ),
    ),
    "spark_plug": TaskGuide(
        task_id="spark_plug",
        est_minutes=40,
        steps=(
            GuideStep(
                instruction_tr="Motor TAMAMEN soğuk olsun. Kontağı kapat. Bujiler ({spark_plug_part}) bobinlerin/kablo başlıklarının altındadır.",
                instruction_en="Engine must be COMPLETELY cold. Ignition off. The plugs ({spark_plug_part}) sit under the coils/leads.",
                warning_tr="Sıcak motorda buji sökmek diş bozar ve yanık riski taşır.",
                warning_en="Removing plugs from a hot engine can strip threads and burn you.",
            ),
            GuideStep(
                instruction_tr="Bobin soketini kilidinden basarak ayır, bobini düz yukarı çek. Tek silindirle başla — karışmaması için sırayla çalış.",
                instruction_en="Unlatch the coil connector and pull the coil straight up. Work one cylinder at a time to avoid mix-ups.",
            ),
            GuideStep(
                instruction_tr="Buji lokmasıyla bujiyi saat yönünün tersine sök.",
                instruction_en="Remove the plug counter-clockwise with a spark plug socket.",
                tool_tr="Buji lokması + uzatma",
                tool_en="Spark plug socket + extension",
            ),
            GuideStep(
                instruction_tr="Yeni bujiyi ELLE başlat (çapraz diş olmasın), sonra yaklaşık 25 Nm ile sık.",
                instruction_en="Start the new plug by HAND (avoid cross-threading), then tighten to roughly 25 Nm.",
                tool_tr="Tork anahtarı",
                tool_en="Torque wrench",
                torque_nm=25,
            ),
            GuideStep(
                instruction_tr="Bobini yerine oturt, soketi kilitle. Diğer silindirlerde aynı işlemi tekrarla.",
                instruction_en="Reseat the coil and latch the connector. Repeat for the remaining cylinders.",
            ),
            GuideStep(
                instruction_tr="Motoru çalıştır: rölanti düzgün mü? Titreme/teklemede kontağı kapat ve tamirciye danış. LPG'li araçta ateşleme sorunu sürerse LPG ayarına dokunma — yetkili LPG servisine git.",
                instruction_en="Start the engine: is idle smooth? If it stumbles, switch off and consult a mechanic. On LPG cars, if misfires persist do NOT touch the LPG system — see an authorised LPG shop.",
                warning_tr="LPG sistemine müdahale etme; LPG işleri yalnızca yetkili serviste yapılır.",
                warning_en="Never work on the LPG system yourself; LPG work belongs to an authorised shop.",
            ),
        ),
    ),
    "coolant": TaskGuide(
        task_id="coolant",
        est_minutes=5,
        steps=(
            GuideStep(
                instruction_tr="Motor TAMAMEN soğukken (en az 2-3 saat bekle) kaputu aç. Yarı saydam genleşme deposunu bul — cam suyu deposuyla karıştırma.",
                instruction_en="With the engine COMPLETELY cold (wait 2-3 hours), open the bonnet. Find the translucent expansion tank — don't confuse it with the washer fluid tank.",
                warning_tr="SICAK MOTORDA KAPAĞI ASLA AÇMA — basınçlı kaynar sıvı fışkırır ve ağır yanığa yol açar.",
                warning_en="NEVER open the cap on a hot engine — pressurised boiling coolant sprays out and causes severe burns.",
            ),
            GuideStep(
                instruction_tr="Kapağı AÇMADAN, depo dışındaki MIN–MAX çizgileri arasında seviye var mı bak.",
                instruction_en="WITHOUT opening the cap, check the level against the MIN–MAX marks on the tank.",
            ),
            GuideStep(
                instruction_tr="Sıvının rengine bak: kırmızı/yeşil/mavi ve berraksa normal. Kahverengi, paslı veya yağlı görünüyorsa ya da seviye sürekli düşüyorsa hiçbir şey ekleme — tamirciye git.",
                instruction_en="Check the colour: red/green/blue and clear is normal. If it looks brown, rusty or oily, or the level keeps dropping, don't top up — see a mechanic.",
                warning_tr="Antifriz zehirlidir; çocuk ve hayvanlardan uzak tut.",
                warning_en="Coolant is toxic; keep it away from children and animals.",
            ),
        ),
    ),
    "brake_check": TaskGuide(
        task_id="brake_check",
        est_minutes=10,
        steps=(
            GuideStep(
                instruction_tr="Bu rehber YALNIZCA gözlem içindir — fren parçası sökme/değiştirme tarifi içermez. Aracı düz zemine al, el frenini çek.",
                instruction_en="This guide is OBSERVATION ONLY — it contains no brake disassembly or replacement instructions. Park on level ground, set the handbrake.",
                warning_tr="Fren can güvenliği sistemidir; her türlü onarım yetkili serviste yapılmalıdır.",
                warning_en="Brakes are a life-safety system; all repairs belong at a professional shop.",
            ),
            GuideStep(
                instruction_tr="Jant aralığından fren diskine bak: derin oluk, çizik veya mavimsi yanık izi var mı? Balata gözle bakıldığında çok ince mi görünüyor?",
                instruction_en="Look at the disc through the wheel: deep grooves, scoring or bluish heat marks? Does the pad look very thin?",
            ),
            GuideStep(
                instruction_tr="Sürüşte gıcırtı, metalik sürtme sesi, pedalda titreme veya uzayan mesafe fark ettiysen aracı zorlamadan fren servisine git.",
                instruction_en="If you've noticed squealing, metallic grinding, pedal vibration or longer stopping distances, drive gently straight to a brake shop.",
                warning_tr="Şüphe varsa sürmeyi bırak — fren arızası ertelenmez.",
                warning_en="When in doubt, stop driving — brake problems can't wait.",
            ),
        ),
    ),
    "tire": TaskGuide(
        task_id="tire",
        est_minutes=10,
        steps=(
            GuideStep(
                instruction_tr="Araç düz zeminde ve soğuk lastikle başla. Direksiyonu çevirerek ön lastik sırtını tamamen görünür yap.",
                instruction_en="Start on level ground with cold tyres. Turn the steering to expose the front tyre tread fully.",
            ),
            GuideStep(
                instruction_tr="Diş derinliğine bak: sırttaki aşınma göstergesi köprücükleri diş seviyesine geldiyse lastik ömrünü doldurmuş olabilir.",
                instruction_en="Check tread depth: if the wear-indicator bars sit level with the tread, the tyre may be done.",
            ),
            GuideStep(
                instruction_tr="Yan duvarda kabarcık (balon), derin kesik veya çatlak ara. Dişler arasında çivi/vida kontrolü yap.",
                instruction_en="Inspect the sidewall for bulges, deep cuts or cracking. Look for nails/screws between the treads.",
                warning_tr="Yan duvarda kabarcık gördüysen o lastikle SÜRME — patlama riski vardır. Lastikçiye git.",
                warning_en="If you see a sidewall bulge, do NOT drive on that tyre — it can blow out. Go to a tyre shop.",
            ),
            GuideStep(
                instruction_tr="Basıncı soğukken kapı fitilindeki etikette yazan değere göre ölç (benzinlikteki basınç saatiyle).",
                instruction_en="Measure pressure cold against the door-jamb label value (use a station gauge).",
                tool_tr="Lastik basınç saati",
                tool_en="Tyre pressure gauge",
            ),
        ),
    ),
    "wiper": TaskGuide(
        task_id="wiper",
        est_minutes=5,
        steps=(
            GuideStep(
                instruction_tr="Kontak kapalıyken silecek kolunu camdan dikleştir. Kol kalkıkken cama düşmesin diye cam üzerine katlanmış bir bez koy.",
                instruction_en="With the ignition off, lift the wiper arm off the glass. Lay a folded cloth on the glass in case the arm snaps back.",
                warning_tr="Yayı kurtulan kol cama sert çarpıp camı çatlatabilir.",
                warning_en="A released arm can snap back hard enough to crack the windscreen.",
            ),
            GuideStep(
                instruction_tr="Lastiğin ortasındaki klipsi bastır ve eski sileceği kol boyunca kaydırarak çıkar.",
                instruction_en="Press the centre clip and slide the old blade off along the arm.",
            ),
            GuideStep(
                instruction_tr="Yeni sileceği 'klik' sesi gelene kadar kaydırarak tak, kolu yavaşça cama bırak. Cam suyu sıkıp silme testini yap.",
                instruction_en="Slide the new blade on until it clicks, lower the arm gently. Spray washer fluid and test.",
            ),
        ),
    ),
    "chain": TaskGuide(
        task_id="chain",
        est_minutes=20,
        steps=(
            GuideStep(
                instruction_tr="Motoru KAPAT ve motosikleti merkez sehpaya al (yoksa paddock sehpası). Vites boşta olsun ki arka teker elle dönsün.",
                instruction_en="Turn the engine OFF and put the bike on its centre/paddock stand. Neutral gear so the rear wheel spins by hand.",
                warning_tr="Motor çalışırken zincire/dişliye asla dokunma — parmak kaptırma ağır yaralanmadır.",
                warning_en="Never touch the chain/sprocket with the engine running — it can take a finger.",
            ),
            GuideStep(
                instruction_tr="Tekerleği elle yavaşça çevirerek zincirin tamamını gözden geçir: kuru/paslı baklalar, donmuş (sıkışmış) halka, sivrilmiş dişli dişi var mı?",
                instruction_en="Slowly turn the wheel by hand and inspect the whole chain: dry/rusty links, stiff (seized) links, hooked sprocket teeth?",
            ),
            GuideStep(
                instruction_tr="Gerginliği kontrol et: alt yolda zinciri parmakla yukarı-aşağı oynat. Genelde ~2-4 cm serbest hareket olmalı (kesin değer için el kitabı).",
                instruction_en="Check tension: push the lower run up/down by finger. Usually ~2-4 cm free play (see your manual for the exact figure).",
                tool_tr="Cetvel / el kitabı",
                tool_en="Ruler / owner's manual",
            ),
            GuideStep(
                instruction_tr="Gerekiyorsa zincir yağını, tekerleği çevirerek baklaların İÇ yüzüne ince ince sür. Fazla yağı sil; lastiğe/frene bulaşmasın.",
                instruction_en="If needed, apply chain lube to the INNER side of the links while turning the wheel. Wipe off excess; keep it off the tyre/brake.",
                tool_tr="Zincir yağı, temiz bez",
                tool_en="Chain lube, clean cloth",
                warning_tr="Fren ve lastik yağdan uzak tutulmalı; kaygan fren/lastik can güvenliği riskidir.",
                warning_en="Keep lube off the brake and tyre; a slippery brake/tyre is a safety risk.",
            ),
            GuideStep(
                instruction_tr="Aşırı sarkık/gergin zincir, donmuş bakla veya sivrilmiş dişli gördüysen ayar/değişimi tamirciye bırak — bu rehber yalnızca yağlama ve kontroldür.",
                instruction_en="If the chain is too loose/tight, has stiff links or hooked sprockets, leave adjustment/replacement to a mechanic — this guide is lube + inspection only.",
            ),
        ),
    ),
    "tire_pressure": TaskGuide(
        task_id="tire_pressure",
        est_minutes=10,
        steps=(
            GuideStep(
                instruction_tr="Lastikler SOĞUKKEN ölç (sürüşten önce ya da en az 2-3 saat sonra). Doğru basınç değerini el kitabından veya sele altı/zincir muhafazası etiketinden öğren.",
                instruction_en="Measure when tyres are COLD (before riding or 2-3 h after). Get the correct pressure from the manual or the under-seat/swingarm label.",
                warning_tr="Sıcak lastikte ölçüm yanıltıcı yüksek çıkar; daima soğukken ölç.",
                warning_en="Hot tyres read falsely high; always measure cold.",
            ),
            GuideStep(
                instruction_tr="Supap kapağını çıkar, basınç saatini supaba sıkıca bastır ve değeri oku. Ön ve arka için ayrı ölç (değerler farklı olabilir).",
                instruction_en="Remove the valve cap, press the gauge firmly onto the valve and read. Measure front and rear separately (values may differ).",
                tool_tr="Lastik basınç saati",
                tool_en="Tyre pressure gauge",
            ),
            GuideStep(
                instruction_tr="Düşükse hava ekle, yüksekse supap iğnesine kısa basarak hava boşalt; sonra tekrar ölç. Üretici değerine getir.",
                instruction_en="If low, add air; if high, briefly press the valve pin to release; re-measure. Match the maker's value.",
            ),
            GuideStep(
                instruction_tr="Supap kapağını tak. Yan duvarda çatlak/balon veya supap dibinde kaçak görürsen o lastikle sürme, tamirciye git.",
                instruction_en="Refit the valve cap. If you see sidewall cracks/bulges or a leak at the valve base, don't ride on it — see a mechanic.",
                warning_tr="Yan duvarda balon/derin çatlak patlama riskidir.",
                warning_en="A sidewall bulge/deep crack is a blowout risk.",
            ),
        ),
    ),
    "clutch_cable": TaskGuide(
        task_id="clutch_cable",
        est_minutes=15,
        steps=(
            GuideStep(
                instruction_tr="Motoru KAPAT, motosikleti sehpaya/desteğe al. Sol gidondaki debriyaj kolunu ve ona bağlı teli bul (sağdaki fren koluyla karıştırma).",
                instruction_en="Turn the engine OFF, put the bike on its stand. Find the clutch lever on the LEFT bar and its cable (don't confuse it with the right brake lever).",
                warning_tr="Fren ve debriyaj kolunu karıştırma; yanlış kol can güvenliği riskidir.",
                warning_en="Don't confuse the brake and clutch levers; the wrong one is a safety risk.",
            ),
            GuideStep(
                instruction_tr="Kol boşluğunu kontrol et: kolun ucunu hafifçe çek; direnç başlamadan önce ~2-3 mm serbest boşluk olmalı (kesin değer el kitabı).",
                instruction_en="Check lever free-play: pull the lever tip lightly; there should be ~2-3 mm free play before resistance (manual for the exact figure).",
            ),
            GuideStep(
                instruction_tr="Teli incele: kılıf çatlak/bükük mü, lifler açılmış/kopmuş mu? Açılmış lif görürsen tele dokunma, sürme ve doğrudan tamirciye git.",
                instruction_en="Inspect the cable: cracked/kinked sheath, frayed/broken strands? If you see fraying, don't touch it, don't ride — go straight to a mechanic.",
                warning_tr="Sürüşte kopan debriyaj teli kontrol kaybına yol açar.",
                warning_en="A clutch cable snapping while riding causes loss of control.",
            ),
            GuideStep(
                instruction_tr="Tel kuruysa ayar parçasından / üst uçtan ince makine yağı damlat ve kolu birkaç kez çekerek dağıt. Fazla yağı sil.",
                instruction_en="If dry, drip light machine oil at the adjuster/top end and work the lever to spread it. Wipe off excess.",
                tool_tr="İnce yağ, temiz bez",
                tool_en="Light oil, clean cloth",
            ),
            GuideStep(
                instruction_tr="Boşluk yanlışsa (debriyaj kavramıyor ya da sürtüyor) ayarı tamirciye bırak; bu rehber yağlama + kontrol içindir.",
                instruction_en="If free-play is off (clutch slips or drags), leave adjustment to a mechanic; this guide is lube + inspection.",
            ),
        ),
    ),
    "headlight": TaskGuide(
        task_id="headlight",
        est_minutes=15,
        steps=(
            GuideStep(
                instruction_tr="Kontağı ve farları kapat. Far yeni yandıysa ampulün soğumasını bekle.",
                instruction_en="Turn off the ignition and lights. If the lamp was just on, let the bulb cool.",
                warning_tr="Ksenon/HID farlar yüksek voltaj içerir — bunlara DOKUNMA, yetkili servise git.",
                warning_en="Xenon/HID units carry high voltage — do NOT touch them; see a professional.",
            ),
            GuideStep(
                instruction_tr="Motor bölmesinden farın arkasındaki toz kapağını çevirerek aç.",
                instruction_en="From the engine bay, twist off the dust cap behind the headlight.",
            ),
            GuideStep(
                instruction_tr="Soketi ayır, ampulü tutucusundan çıkar. Konektörde erime/yanık izi varsa elektrik arızası olabilir — tamirciye git.",
                instruction_en="Unplug the connector and release the bulb. If the connector shows melting/burn marks, there may be an electrical fault — see a mechanic.",
            ),
            GuideStep(
                instruction_tr="Yeni halojen ampulün CAM kısmına çıplak elle dokunma; temiz bez/eldivenle tak. Kapağı kapat, farı yakıp test et.",
                instruction_en="Never touch the GLASS of a new halogen bulb bare-handed; fit it with a clean cloth/gloves. Refit the cap and test.",
                warning_tr="Cama bulaşan cilt yağı ampulü erken patlatır.",
                warning_en="Skin oil on the glass makes the bulb fail early.",
            ),
        ),
    ),
}


def get_guide(task_id: str) -> TaskGuide | None:
    return GUIDES.get(task_id)


def _is_blank_value(value: object) -> bool:
    """Bir spec değeri yer tutucu/boş mu? None, boş string, sayısal sıfır ve yalnızca
    tire/çizgi içeren string'ler (örn. "—", "-") boş sayılır — aksi halde "0.0 L yağ
    koy" / "— anahtarıyla sök" gibi yanıltıcı talimatlar basılır (safety-auditor)."""
    if value is None:
        return True
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip().strip("-—–") == ""
    return False


def fill_template(text: str, spec_values: dict[str, object], lang: str) -> str:
    """`{anahtar}` yer tutucularını spec'ten doldurur; yoksa genel ifade kullanır."""
    fallbacks = _FALLBACKS_TR if lang == "tr" else _FALLBACKS_EN
    out = text
    for key, fallback in fallbacks.items():
        token = "{" + key + "}"
        if token in out:
            value = spec_values.get(key)
            out = out.replace(token, fallback if _is_blank_value(value) else str(value))
    return out
