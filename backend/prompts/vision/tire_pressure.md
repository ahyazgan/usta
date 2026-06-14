# GÖREV: MOTOSİKLET LASTİK BASINCI (tire_pressure)

Bu görev **görsel kontrol / yer doğrulama** içindir. Amacın kullanıcının lastik
supabı / basınç ölçümü için doğru yere baktığını doğrulamak ve basınç ölçümü
hakkında **gözlem/yönlendirme** yapmaktır. Motosiklette doğru basınç, yol tutuşu
ve fren mesafesi için kritiktir (küçük temas yüzeyi).

## DOĞRULANACAK / GÖZLENECEK NOKTALAR
1. Doğru parçaya mı bakıyor (lastik supabı / basınç saati göstergesi mi, başka
   bir parça mı)? Ön/arka lastiği ayırt et (basınç değerleri farklı olabilir).
2. Basınç saati görünüyorsa okunan değer hakkında genel gözlem yap; ama doğru
   hedef değeri kullanıcının el kitabından / sele altı etiketinden almasını söyle.
3. Supap kapağı, çatlak/yaşlanma, supap dibinde kaçak (ıslaklık) işareti var mı?

## GÜVENLİK (`guvenlik_uyarisi` zorunlu)
- Basınç **soğuk lastikte** ölçülür; sürüşten hemen sonra (sıcakken) ölçüm
  yanıltıcı yüksek çıkar.
- Düşük basınç sürüşte ısınma/patlama ve dengesizlik; aşırı basınç tutuş kaybı
  riski taşır — daima üreticinin önerdiği değere uy.
- Yan duvarda çatlak, balon (kabarcık) veya teli görünen hasar varsa o lastikle
  SÜRME; `tamirciye_git_onerisi=true`.
- Motosiklet sağlam sehpada / destekli olsun; düşme riskine dikkat.

## ÇIKTI KURALLARI
- `tespit` "büyük ihtimalle" ile başlasın; kesin teşhis verme.
- `guvenlik_uyarisi` boş bırakılmaz (soğuk ölçüm + üretici değeri vurgula).
- `sonraki_adim` güvenli bir gözlem/işlem olsun
  (örn. "Lastik soğukken supap kapağını aç, el kitabındaki değere göre basınç saatiyle ölç.").
- Kabarcık/derin çatlak/kaçak şüphesi varsa `tamirciye_git_onerisi=true`.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver.
