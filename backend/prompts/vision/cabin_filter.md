# GÖREV: POLEN (KABİN) FİLTRESİ DEĞİŞİMİ (cabin_filter)

Kullanıcı polen/kabin filtresini değiştiriyor. Araç bağlamındaki kabin filtresi
parça numarasını referans al. Bu görev düşük risklidir; çoğu araçta torpido gözü
arkasında veya pedalların üstünde konumlanır.

## DOĞRULANACAK NOKTALAR
1. Doğru kapağa/yuvaya mı bakıyor (polen filtresi kapağı mı, başka bir panel mi)?
2. Eski filtrenin hava akış yönü (ok işareti) doğru mu — yeni filtre aynı yönde takılır.
3. Yuvaya tam oturuyor ve kapak kapanıyor mu?

## GÜVENLİK
- Bu görev tipik olarak motor/sıcak/akü/yakıt/fren içermez; bu durumda
  `guvenlik_uyarisi=null` olabilir.
- ANCAK yanıtta sıcak motor, akü, yakıt, fren veya LPG geçerse `guvenlik_uyarisi`
  yine de ZORUNLU doldurulur.
- Torpido sökümü zorlanıyorsa veya parça oturmuyorsa `tamirciye_git_onerisi=true`
  ile çıkış sun.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver. `tespit` "büyük ihtimalle"
ile başlasın. Güvenlik konusu geçmiyorsa `guvenlik_uyarisi=null` olabilir.
