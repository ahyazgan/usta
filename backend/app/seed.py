"""Demo verisi tohumlama (idempotent).

Çalıştır:  python -m app.seed
Bir demo kullanıcı ve TR araç parkından birkaç araç oluşturur; spec'ler
katalogdan otomatik dolar. Üretim için değildir; geliştirme/demo amaçlıdır.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta

from sqlalchemy import select

# Windows konsolu (cp1254) "✓" gibi karakterlerde çöker; çıktıyı UTF-8'e sabitle.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from .core.security import hash_password
from .database import SessionLocal, create_all
from .domain.catalog import find_spec
from .domain.enums import FuelType, VehicleType
from .domain.models import Mechanic, User, Vehicle, VehicleSpec

DEMO_EMAIL = "demo@usta.app"
DEMO_PASSWORD = "demoparola1234"

# Demo tarihleri bugüne göreli — biri yaklaşan (sigorta), biri ileride (muayene).
_TODAY = date.today()
DEMO_VEHICLES = [
    {"make": "Fiat", "model": "Egea", "year": 2019, "plate": "34 ABC 123", "fuel_type": FuelType.lpg, "engine_code": "843A1000", "current_km": 84210,
     "muayene_date": _TODAY + timedelta(days=120), "sigorta_date": _TODAY + timedelta(days=18)},
    {"make": "Renault", "model": "Clio", "year": 2018, "plate": "06 XYZ 45", "fuel_type": FuelType.dizel, "engine_code": "K9K", "current_km": 138420,
     "muayene_date": _TODAY + timedelta(days=45), "sigorta_date": _TODAY + timedelta(days=200)},
    {"make": "Toyota", "model": "Corolla", "year": 2016, "plate": "35 KL 1234", "fuel_type": FuelType.benzin, "engine_code": "1ZR-FAE", "current_km": 96000},
    {"make": "Honda", "model": "CB125", "year": 2021, "plate": "34 MT 567", "fuel_type": FuelType.benzin, "vehicle_type": VehicleType.motosiklet, "engine_code": "JC64", "current_km": 18250},
]

# Küratörlü demo tamirciler (gerçek tedarik iş-geliştirme adımıdır; bunlar örnek).
DEMO_MECHANICS = [
    {"name": "Usta Garaj Oto Servis", "city": "İstanbul", "district": "Kadıköy", "phone": "+902161112233", "whatsapp": "+905321112233", "address": "Caferağa Mah. Moda Cd. No:12", "maps_url": "https://maps.google.com/?q=Kadıköy+oto+servis", "specialties": "Genel bakım, motor, fren", "systems": "motor,fren,filtre", "verified": True},
    {"name": "Anadolu Oto Elektrik", "city": "İstanbul", "district": "Ümraniye", "phone": "+902162223344", "whatsapp": "+905332223344", "address": "Atatürk Mah. Alemdağ Cd. No:45", "maps_url": "https://maps.google.com/?q=Ümraniye+oto+elektrik", "specialties": "Akü, marş, alternatör, far", "systems": "elektrik,atesleme", "verified": True},
    {"name": "Hız Lastik & Rot Balans", "city": "İstanbul", "district": "Maltepe", "phone": "+902163334455", "whatsapp": None, "address": "Bağlarbaşı Mah. Bağdat Cd. No:201", "maps_url": "https://maps.google.com/?q=Maltepe+lastik", "specialties": "Lastik, rot-balans, süspansiyon", "systems": "lastik,suspansiyon", "verified": False},
    {"name": "Başkent Oto LPG & Servis", "city": "Ankara", "district": "Çankaya", "phone": "+903124445566", "whatsapp": "+905354445566", "address": "Kızılay Mah. Atatürk Blv. No:78", "maps_url": "https://maps.google.com/?q=Çankaya+lpg+servis", "specialties": "LPG, genel bakım, motor", "systems": "motor,atesleme,filtre", "verified": True},
    {"name": "Ege Fren & Mekanik", "city": "İzmir", "district": "Bornova", "phone": "+902325556677", "whatsapp": "+905365556677", "address": "Erzene Mah. Ankara Cd. No:9", "maps_url": "https://maps.google.com/?q=Bornova+fren", "specialties": "Fren, debriyaj, şanzıman", "systems": "fren,sanziman", "verified": True},
]


async def seed() -> None:
    await create_all()
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            await db.flush()
            print(f"+ demo kullanıcı: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print(f"= demo kullanıcı zaten var: {DEMO_EMAIL}")

        for data in DEMO_VEHICLES:
            exists = await db.scalar(
                select(Vehicle).where(
                    Vehicle.user_id == user.id,
                    Vehicle.make == data["make"],
                    Vehicle.model == data["model"],
                    Vehicle.year == data["year"],
                )
            )
            if exists:
                print(f"= araç zaten var: {data['make']} {data['model']} {data['year']}")
                continue
            vehicle = Vehicle(user_id=user.id, **data)
            spec_in = find_spec(
                data["make"], data["model"], data["year"],
                fuel_type=data["fuel_type"], engine_code=data["engine_code"],
                vehicle_type=data.get("vehicle_type"),
            )
            if spec_in is not None:
                vehicle.spec = VehicleSpec(**spec_in.model_dump())
            db.add(vehicle)
            tag = "spec✓" if spec_in else "spec yok"
            print(f"+ araç: {data['make']} {data['model']} {data['year']} ({tag})")

        # Küratörlü tamirciler (idempotent: ada göre).
        for m in DEMO_MECHANICS:
            exists = await db.scalar(select(Mechanic).where(Mechanic.name == m["name"]))
            if exists:
                continue
            db.add(Mechanic(**m))
            print(f"+ tamirci: {m['name']} ({m['city']})")

        await db.commit()
    print("Tohumlama tamam.")


if __name__ == "__main__":
    asyncio.run(seed())
