"""ORM modelleri (SQLAlchemy 2.0 tipli)."""

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import AIKind, FuelType, SubscriptionTier, VehicleType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(SubscriptionTier), default=SubscriptionTier.free, nullable=False
    )
    # KVKK açık rızası (null = henüz seçim yapılmadı; varsayılan KAPALI).
    # consent_analytics: davranış analitiği; consent_data: anonim küme kullanımı.
    consent_analytics: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    consent_data: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    plate: Mapped[str | None] = mapped_column(String(15), nullable=True)
    engine_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Tarih-bazlı hatırlatıcılar (ISO YYYY-MM-DD; km değil takvim).
    muayene_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sigorta_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(SAEnum(FuelType), nullable=False)
    # Araç türü (görev uygunluğunu etkiler). Eski kayıtlarda null = araba.
    vehicle_type: Mapped[VehicleType | None] = mapped_column(
        # native_enum=False: string-backed (VARCHAR). vehicle_type mevcut vehicles
        # tablosuna sonradan VARCHAR(12) migration'la eklendi; Postgres native
        # 'vehicletype' enum tipi hiç oluşmadı → enum karşılaştırmalı sorgular
        # (fiyat tahmini) 500 veriyordu. name==value olduğu için veri değişmez.
        SAEnum(VehicleType, native_enum=False, length=12),
        nullable=True,
    )
    current_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped["User"] = relationship(back_populates="vehicles")
    spec: Mapped["VehicleSpec | None"] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", uselist=False
    )
    logs: Mapped[list["MaintenanceLog"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class VehicleSpec(Base):
    """Araca özel bakım verileri (yağ tıpası ölçüsü, parça numaraları...)."""

    __tablename__ = "vehicle_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, index=True
    )
    oil_spec: Mapped[str | None] = mapped_column(String(60), nullable=True)
    oil_capacity_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    oil_drain_bolt_size: Mapped[str | None] = mapped_column(String(40), nullable=True)
    oil_drain_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    oil_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    air_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cabin_filter_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    spark_plug_part: Mapped[str | None] = mapped_column(String(60), nullable=True)
    battery_spec: Mapped[str | None] = mapped_column(String(60), nullable=True)
    battery_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    transmission_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="spec")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    task: Mapped[str] = mapped_column(String(60), nullable=False)
    km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Bu bakımı tetikleyen AI teşhisi (rehber kamera doğrulamasıyla bitince bağlanır).
    ai_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="SET NULL"), nullable=True
    )
    # Kullanıcının beyan ettiği gerçek maliyet (TL; opsiyonel) — maliyet endeksi.
    cost_try: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="logs")


class AISession(Base):
    """Her AI çağrısı için token kullanımını + teşhis özetini loglar.

    Token alanları maliyet denetimi içindir; özet alanlar (task/tespit/guven/
    tamirciye_git) mobil "Teşhis Geçmişi" listesini besler. Özet, güvenlik
    kuralları ZORLANDIKTAN SONRAKİ metinden yazılır.
    """

    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[AIKind] = mapped_column(SAEnum(AIKind), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    # Teşhis özeti (geçmiş listesi için; eski kayıtlarda null olabilir).
    task: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tespit: Mapped[str | None] = mapped_column(String(500), nullable=True)
    guven: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tamirciye_git: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Yapılandırılmış kategori: görüntüde görev id'si, seste ses_kategorisi.
    kategori: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Arıza taksonomisi: sorgulanabilir araç sistemi (motor/fren/elektrik…).
    ariza_sistem: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Kullanıcı geri bildirimi: teşhis doğru çıktı mı? (👍/👎; null = oylanmadı)
    # Bu etiket, veri setini doğrulanmış arıza-örüntü verisine çevirir.
    feedback_dogru: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Kapanış sinyali: sorun nasıl çözüldü? (tahmin doğruluğunu ölçer)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Tamirci çözdüyse beyan edilen ödeme (TL) — sistem fiyat bandının yakıtı.
    # Yalnızca resolution=tamirci_cozdu olduğunda yazılır (bandı kirletmez).
    cost_try: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Mechanic(Base):
    """Küratörlü tamirci dizini (Faz C MVP — gerçek tedarik iş-geliştirme adımı).

    `systems` = ilgilendiği araç sistemleri (virgülle, ArizaSistem değerleri);
    boş = genel. Triyaj/teşhis sonrası kullanıcı buradan tamirci bulur.
    """

    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(60), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    maps_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    specialties: Mapped[str | None] = mapped_column(String(200), nullable=True)
    systems: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MechanicLead(Base):
    """Tamirci yönlendirme sinyali (lead-gen gelir modelinin temeli).

    Kullanıcı bir tamirciyi aradığında/WhatsApp veya yol tarifi açtığında kaydedilir;
    ileride tamircilerden lead başına ücretlendirme bu tabloya dayanır.
    """

    __tablename__ = "mechanic_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mechanic_id: Mapped[int] = mapped_column(
        ForeignKey("mechanics.id", ondelete="CASCADE"), index=True
    )
    ai_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # call|whatsapp|directions
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PartLead(Base):
    """Parça 'Satın Al' niyeti (affiliate ölçüm + ortaklık kozu).

    Kullanıcı bir parçanın satın-al linkine dokununca kaydedilir; admin paneli
    bunu toplar ("şu kadar parça-alım niyeti ürettik" → perakendeci görüşmesi).
    """

    __tablename__ = "part_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    task: Mapped[str | None] = mapped_column(String(60), nullable=True)
    part_label: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LiveUsage(Base):
    """Canlı sesli rehber oturum kullanımı (dakika sayacı + maliyet freni).

    Oturum başında 0 saniyeyle açılır; istemci bitince süreyi bildirir. Aylık
    toplam, ücretsiz katman limitiyle karşılaştırılır (premium = sınırsız).
    """

    __tablename__ = "live_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    task: Mapped[str | None] = mapped_column(String(60), nullable=True)
    lang: Mapped[str] = mapped_column(String(5), default="tr")
    seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RefreshToken(Base):
    """Yenileme token'ları sha256 hash olarak saklanır (düz metin DB'de tutulmaz)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
