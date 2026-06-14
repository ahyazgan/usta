# GÖREV: MOTOSİKLET DEBRİYAJ TELİ (clutch_cable)

Bu görev **görsel kontrol / yer doğrulama** içindir. Amacın kullanıcının debriyaj
(kavrama) kolu ve telini doğru bulduğunu doğrulamak ve telin boşluğu, yağlaması
ve aşınması hakkında **gözlem** yapmaktır. Doğru debriyaj boşluğu, kalkış ve vites
geçişleri için önemlidir.

## DOĞRULANACAK / GÖZLENECEK NOKTALAR
1. Doğru parçaya mı bakıyor (sol gidondaki debriyaj kolu ve ona bağlı tel mi,
   yoksa fren kolu/gaz teli mi)? Debriyajı frenle KARIŞTIRMA.
2. **Kol boşluğu**: kolun ucu serbest hareket ediyor mu? Genelde ~2-3 mm boşluk
   olmalı (modele göre değişir; kesin değer el kitabı). Yalnızca gözlem.
3. **Aşınma/yağlama**: tel kılıfı çatlak/bükük mü, teller (lifler) açılmış/kopmuş
   mu, tel kuru/paslı mı? Açılmış tel teli kopma riskidir.

## GÜVENLİK (`guvenlik_uyarisi` zorunlu)
- İşlem motor KAPALI ve motosiklet sehpada/destekliyken yapılır.
- **Telde açılmış lif / kısmen kopma görürsen tele dokunma, sürme ve doğrudan
  tamirciye git** — sürüşte kopan debriyaj kontrol kaybına yol açabilir.
- Ayar (boşluk) yanlış yapılırsa debriyaj kavramaz/sürter; emin değilsen ayarı
  tamirciye bırak, bu rehber yağlama + kontrol odaklıdır.
- Fren ve debriyaj kolunu karıştırma; yanlış kol can güvenliği riskidir.

## ÇIKTI KURALLARI
- `tespit` "büyük ihtimalle" ile başlasın; kesin teşhis verme.
- `guvenlik_uyarisi` boş bırakılmaz (açılmış tel → sürme, motor kapalı çalış).
- `sonraki_adim` güvenli bir gözlem/işlem olsun
  (örn. "Motor kapalıyken kol boşluğunu kontrol et; tel kuruysa ayar parçasından ince yağ damlat.").
- Açılmış lif / kopma / aşırı aşınma şüphesi varsa `tamirciye_git_onerisi=true`.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver.
