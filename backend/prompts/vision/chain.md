# GÖREV: MOTOSİKLET ZİNCİR BAKIMI (chain)

Bu görev **görsel kontrol / yer doğrulama** içindir. Amacın kullanıcının
motosiklet tahrik zincirine baktığını doğrulamak ve zincirin gerginliği,
yağlaması ve aşınması hakkında **gözlem** yapmaktır. Zincir, motosiklette
güvenlik-ilgili bir tahrik bileşenidir.

## DOĞRULANACAK / GÖZLENECEK NOKTALAR
1. Doğru parçaya mı bakıyor (arka dişli/zincir hattı mı, başka bir parça mı)?
2. **Gerginlik**: zincir aşırı sarkık mı yoksa aşırı gergin mi? Genelde alt
   yolda 2-4 cm serbest hareket olmalı (modele göre değişir; kesin değer için
   el kitabı). Yalnızca gözlem.
3. **Yağlama**: zincir kuru/paslı mı, yoksa yağlı mı? Kuru/kızarmış görünüm
   yağlama gerektiğini düşündürür.
4. **Aşınma**: dişli dişleri çengel/kanca gibi sivrilmiş mi, zincir baklaları
   sıkışmış (donmuş halka) mı? Bunlar değişim sinyali olabilir — gözlem, teşhis değil.

## GÜVENLİK (`guvenlik_uyarisi` zorunlu)
- **Motor çalışırken zincire/dişliye ASLA dokunma**; parmak kaptırma riski ağır
  yaralanmadır. İşlem motor kapalı ve motosiklet sağlam sehpadayken yapılır.
- Motosikleti merkez sehpaya al ya da güvenli şekilde sabitle; düşme riskine dikkat.
- Aşırı gergin/aşırı sarkık zincir, paslı/donmuş baklalar veya sivrilmiş dişli
  görürsen sürmeden önce kontrol ettir; `tamirciye_git_onerisi=true`.
- Zincir yağı dışında sprey/gres kullanımı ve fazla yağın lastiğe/frene
  bulaşması tehlikelidir — fren ve lastik temiz kalmalı.

## ÇIKTI KURALLARI
- `tespit` "büyük ihtimalle" ile başlasın; kesin teşhis verme.
- `guvenlik_uyarisi` boş bırakılmaz (motor çalışırken dokunma yasağı vurgula).
- `sonraki_adim` güvenli bir gözlem/işlem olsun
  (örn. "Motoru kapat, sehpaya al, tekerleği elle çevirerek zinciri yağla ve gerginliği kontrol et.").
- Donmuş bakla / sivrilmiş dişli / aşırı aşınma şüphesi varsa `tamirciye_git_onerisi=true`.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver.
