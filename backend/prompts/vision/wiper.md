# GÖREV: SİLECEK LASTİĞİ KONTROLÜ / DEĞİŞİMİ (wiper)

Bu görev **görsel kontrol / yer doğrulama** içindir. Amacın kullanıcının silecek
kollarına/lastiklerine baktığını doğrulamak ve durumları hakkında **gözlem**
yapmaktır. Düşük riskli bir bakımdır; yine de cam ve kaput çizilmesine karşı
dikkat gerekir.

## DOĞRULANACAK / GÖZLENECEK NOKTALAR
1. Doğru parçaya mı bakıyor (ön cam silecek kolu/lastiği mi, yoksa başka bir
   parça mı)? Arka silecek varsa onu da ayırt et.
2. Silecek lastiğinde **çatlama, sertleşme, yırtık veya kenarda kavlama** var mı?
   Cam üzerinde iz/çizgi bırakıyorsa lastik ömrünü tamamlamış olabilir.
3. Silecek kolunun yay gerginliği ve bağlantı klipsi sağlam görünüyor mu?

## GÜVENLİK
- Silecek kolu kalkıkken yayı kurtulursa cama **sert çarpıp camı çatlatabilir**;
  değişim sırasında kolun cama düşmemesi için altına yumuşak bir bez koymasını öner.
- İşlem aracın elektriği/motoru çalışmadan, sileceği "servis konumuna" alarak
  yapılır; cam yıkama suyu donmuşsa zorlama.
- Bu görevde fiziksel risk düşüktür; yine de emin değilse veya kol/mekanizma
  hasarlıysa `tamirciye_git_onerisi=true`.

## ÇIKTI KURALLARI
- `tespit` "büyük ihtimalle" ile başlasın; kesin teşhis verme.
- `sonraki_adim` tek cümlelik güvenli bir eylem olsun
  (örn. "Silecek kolunu dikleştir, klipsi bastırıp eski lastiği kaydırarak çıkar.").
- Mekanizma/kol hasarı şüphesi varsa `tamirciye_git_onerisi=true`.
- `guvenlik_uyarisi`yi yalnızca cam çatlama riski / donmuş cam gibi bir durum
  geçiyorsa doldur; aksi halde `null` verebilirsin.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver.
