"""Demo verisi tohumlama (idempotent).

Çalıştır:  python -m app.seed
Bir demo kullanıcı ve TR araç parkından birkaç araç oluşturur; spec'ler
katalogdan otomatik dolar. Üretim için değildir; geliştirme/demo amaçlıdır.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from .core.security import hash_password
from .database import SessionLocal, create_all
from .domain.catalog import find_spec
from .domain.enums import FuelType
from .domain.models import User, Vehicle, VehicleSpec

DEMO_EMAIL = "demo@usta.app"
DEMO_PASSWORD = "demoparola1234"

DEMO_VEHICLES = [
    {"make": "Fiat", "model": "Egea", "year": 2019, "fuel_type": FuelType.lpg, "engine_code": "843A1000", "current_km": 84210},
    {"make": "Renault", "model": "Clio", "year": 2018, "fuel_type": FuelType.dizel, "engine_code": "K9K", "current_km": 138420},
    {"make": "Toyota", "model": "Corolla", "year": 2016, "fuel_type": FuelType.benzin, "engine_code": "1ZR-FAE", "current_km": 96000},
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
            )
            if spec_in is not None:
                vehicle.spec = VehicleSpec(**spec_in.model_dump())
            db.add(vehicle)
            tag = "spec✓" if spec_in else "spec yok"
            print(f"+ araç: {data['make']} {data['model']} {data['year']} ({tag})")

        await db.commit()
    print("Tohumlama tamam.")


if __name__ == "__main__":
    asyncio.run(seed())
