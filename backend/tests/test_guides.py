"""Rehber (guide) ve özet (summary) endpoint testleri.

Kapsam:
  - GET /v1/vehicles/{id}/tasks/{task_id}/guide — task_guide
  - GET /v1/vehicles/{id}/summary            — vehicle_summary

Claude API bu endpoint'lerde KULLANILMIYOR; mock gerekmez.
"""

from __future__ import annotations

import pytest

from .conftest import create_vehicle, register_and_login


# =========================================================================== #
# GET /v1/vehicles/{vehicle_id}/tasks/{task_id}/guide
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_oil_change_happy(client):
    """Happy path: LPG Egea + oil_change → 200, adımlar dolu, spec dolgusu çalışıyor."""
    # Arrange
    headers = await register_and_login(client, "guide1@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    # Act
    r = await client.get(f"/v1/vehicles/{vid}/tasks/oil_change/guide", headers=headers)

    # Assert — HTTP + şema
    assert r.status_code == 200
    body = r.json()
    assert body["task_id"] == "oil_change"
    assert body["title_tr"] and body["title_en"]
    assert body["risk"] in ("dusuk", "orta", "yuksek")
    assert body["est_minutes"] > 0
    assert len(body["steps"]) > 0

    # Her adımda en az instruction_tr ve instruction_en dolu.
    for step in body["steps"]:
        assert step["instruction_tr"], "instruction_tr boş olamaz"
        assert step["instruction_en"], "instruction_en boş olamaz"

    # Spec dolgusu: conftest'te oil_drain_bolt_size="13mm"
    # → bir adımda veya alet alanında "13mm" geçmeli.
    all_text = " ".join(
        " ".join(filter(None, [s["instruction_tr"], s.get("tool_tr", "")]))
        for s in body["steps"]
    )
    assert "13mm" in all_text, "spec değeri (13mm) adımlara yansımamış"

    # Ham yer tutucu ({oil_drain_bolt_size}) yanıtta GEÇMEMELİ.
    full_json_text = r.text
    assert "{oil_drain_bolt_size}" not in full_json_text, "ham yer tutucu yanıtta kaldı"
    assert "{oil_spec}" not in full_json_text
    assert "{oil_capacity_l}" not in full_json_text
    assert "{oil_filter_part}" not in full_json_text


@pytest.mark.asyncio
async def test_guide_includes_prep_parts(client):
    """Hazırlık listesi: araca özel parça numaraları guide yanıtında gelir."""
    headers = await register_and_login(client, "guideprep@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    body = (await client.get(f"/v1/vehicles/{vid}/tasks/oil_change/guide", headers=headers)).json()
    parts = body["parts"]
    assert len(parts) >= 3
    values = {p["value"] for p in parts}
    assert "55256470" in values and "5W-30" in values  # yağ filtresi + motor yağı
    assert "Yağ filtresi" in {p["label_tr"] for p in parts}
    assert {"label_tr", "label_en", "value", "buy_url"} <= parts[0].keys()
    # Affiliate iskeleti: varsayılan şablonla her parçada "Satın Al" linki var.
    filt = next(p for p in parts if p["value"] == "55256470")
    assert filt["buy_url"] is not None and "55256470" in filt["buy_url"]

    # Parça eşlemesi olmayan görevde liste boş.
    fren = (await client.get(f"/v1/vehicles/{vid}/tasks/brake_check/guide", headers=headers)).json()
    assert fren["parts"] == []


@pytest.mark.asyncio
async def test_guide_requires_auth_401(client):
    """Token olmadan istek → 401."""
    r = await client.get("/v1/vehicles/1/tasks/oil_change/guide")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_guide_unknown_task_404(client):
    """Var olmayan görev id → 404."""
    headers = await register_and_login(client, "guide2@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(
        f"/v1/vehicles/{vehicle['id']}/tasks/olmayan_gorev/guide",
        headers=headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_guide_inapplicable_fuel_404(client):
    """Dizel araçta spark_plug (buji yok) → 404."""
    headers = await register_and_login(client, "guide3@usta.app")

    # Dizel araç oluştur
    diesel = await client.post(
        "/v1/vehicles",
        json={
            "make": "Renault",
            "model": "Clio",
            "year": 2020,
            "fuel_type": "dizel",
            "engine_code": "K9K",
        },
        headers=headers,
    )
    assert diesel.status_code == 201
    vid = diesel.json()["id"]

    r = await client.get(
        f"/v1/vehicles/{vid}/tasks/spark_plug/guide",
        headers=headers,
    )
    assert r.status_code == 404


# =========================================================================== #
# Güvenlik assert'leri — mechanic_note zorunluluğu
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_mechanic_note_present_in_all_guides(client):
    """Her rehberde mechanic_note_tr dolu ve 'tamirciye git' ifadesi geçiyor."""
    headers = await register_and_login(client, "guide4@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    # LPG Egea'ya uygulanabilir tüm görevler.
    applicable_tasks = [
        "oil_change", "spark_plug", "battery", "brake_check",
        "air_filter", "cabin_filter", "coolant", "tire", "wiper", "headlight",
    ]
    for task_id in applicable_tasks:
        r = await client.get(
            f"/v1/vehicles/{vid}/tasks/{task_id}/guide",
            headers=headers,
        )
        assert r.status_code == 200, f"{task_id} → {r.status_code}"
        body = r.json()
        note = body.get("mechanic_note_tr", "")
        assert note, f"{task_id}: mechanic_note_tr boş"
        assert "tamirciye git" in note.lower(), (
            f"{task_id}: mechanic_note_tr 'tamirciye git' içermiyor → '{note}'"
        )


# =========================================================================== #
# Güvenlik assert'i — coolant sıcak motor yasağı
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_coolant_hot_engine_warning(client):
    """Coolant rehberinde en az bir adımda warning_tr dolu
    VE 'AÇMA' veya 'sıcak' ifadesi geçiyor."""
    headers = await register_and_login(client, "guide5@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(
        f"/v1/vehicles/{vehicle['id']}/tasks/coolant/guide",
        headers=headers,
    )
    assert r.status_code == 200
    steps = r.json()["steps"]

    warning_steps = [s for s in steps if s.get("warning_tr")]
    assert warning_steps, "coolant rehberinde hiç warning_tr dolu adım yok"

    combined_warnings = " ".join(s["warning_tr"] for s in warning_steps).upper()
    assert "AÇMA" in combined_warnings or "SICAK" in combined_warnings, (
        f"coolant uyarısında 'AÇMA' veya 'sıcak' yok → {combined_warnings}"
    )


# =========================================================================== #
# Güvenlik assert'i — brake_check gözlem-odaklı (söküm tarifi yok)
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_brake_check_no_disassembly(client):
    """Fren kontrolü rehberi gözlem-odaklı olmalı:
    - adımlarda 'sök' fiili emir kipinde geçmemeli (söküm tarifi yok)
    - rehber, söküm/değiştirme yapmadığını AÇIKÇA beyan etmeli ('içermez')
    """
    headers = await register_and_login(client, "guide6@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(
        f"/v1/vehicles/{vehicle['id']}/tasks/brake_check/guide",
        headers=headers,
    )
    assert r.status_code == 200
    steps = r.json()["steps"]

    all_instructions = " ".join(s["instruction_tr"] for s in steps)

    # Rehber, söküm/değiştirme talimatı VERMEDIĞINI beyan etmeli.
    assert "içermez" in all_instructions.lower(), (
        "brake_check rehberi söküm tarifi içermediğini beyan etmiyor"
    )

    # Emir kipi söküm fiili (ör. "fren diskini sök", "balatayı sök") geçmemeli.
    # "sökme/değiştirme tarifi içermez" gibi reddetme cümleleri kabul edilir;
    # sadece tek başına "sök" emir fiili (ardından boşluk, nokta veya virgül gelen)
    # bir söküm talimatı sayılır.
    import re
    imperative_sok = re.compile(r"\bsök\b(?!\s*me\b|\s*tür|\s*üm)", re.IGNORECASE)
    for i, step in enumerate(steps, start=1):
        instruction = step["instruction_tr"]
        assert not imperative_sok.search(instruction), (
            f"brake_check adım {i} emir kipinde söküm fiili içeriyor: '{instruction}'"
        )


# =========================================================================== #
# Spec dolgusu — fallback (spec verilmemiş araç)
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_spec_fallback_no_placeholders(client):
    """Spec verilmemiş araçta ham yer tutucu GEÇMEMELİ; genel ifadeye düşmeli."""
    headers = await register_and_login(client, "guide7@usta.app")

    # Spec'siz araç
    bare = await client.post(
        "/v1/vehicles",
        json={
            "make": "Toyota",
            "model": "Corolla",
            "year": 2018,
            "fuel_type": "benzin",
            "engine_code": "1ZR",
        },
        headers=headers,
    )
    assert bare.status_code == 201
    vid = bare.json()["id"]

    r = await client.get(
        f"/v1/vehicles/{vid}/tasks/oil_change/guide",
        headers=headers,
    )
    assert r.status_code == 200
    full_text = r.text

    for key in (
        "oil_spec", "oil_capacity_l", "oil_drain_bolt_size",
        "oil_filter_part", "spark_plug_part", "battery_spec",
    ):
        placeholder = "{" + key + "}"
        assert placeholder not in full_text, (
            f"ham yer tutucu yanıtta kaldı: {placeholder}"
        )


# =========================================================================== #
# GET /v1/vehicles/{vehicle_id}/summary
# =========================================================================== #


@pytest.mark.asyncio
async def test_summary_empty_logs(client):
    """Log yokken summary {maintenance_count: 0, savings_try: 0} döner."""
    headers = await register_and_login(client, "sum1@usta.app")
    vehicle = await create_vehicle(client, headers)
    r = await client.get(f"/v1/vehicles/{vehicle['id']}/summary", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["maintenance_count"] == 0
    assert body["savings_try"] == 0


@pytest.mark.asyncio
async def test_summary_with_logs(client):
    """oil_change (400 TL) + brake_check (500 TL) → {2, 900}."""
    headers = await register_and_login(client, "sum2@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]

    # oil_change logu ekle
    r1 = await client.post(
        f"/v1/vehicles/{vid}/logs",
        json={"task": "oil_change", "km": 80000},
        headers=headers,
    )
    assert r1.status_code == 201

    # brake_check logu ekle
    r2 = await client.post(
        f"/v1/vehicles/{vid}/logs",
        json={"task": "brake_check", "km": 80000},
        headers=headers,
    )
    assert r2.status_code == 201

    # Summary kontrolü
    r = await client.get(f"/v1/vehicles/{vid}/summary", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["maintenance_count"] == 2
    assert body["savings_try"] == 900  # 400 + 500


@pytest.mark.asyncio
async def test_summary_requires_auth_401(client):
    """Token olmadan summary isteği → 401."""
    r = await client.get("/v1/vehicles/1/summary")
    assert r.status_code == 401


# =========================================================================== #
# 429 — rate limit (guide endpoint)
# =========================================================================== #


@pytest.mark.asyncio
async def test_guide_rate_limit_429(client):
    """Rate limiti tüketince guide endpoint 429 döner."""
    from app.core.rate_limit import get_rate_limiter

    headers = await register_and_login(client, "guide_rl@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    limiter = get_rate_limiter()

    # Limiti sıfırla, sonra bir istek at ve sayacı limit'e taşı.
    limiter.reset()
    # İlk istek geçmeli.
    r = await client.get(
        f"/v1/vehicles/{vid}/tasks/oil_change/guide", headers=headers
    )
    assert r.status_code == 200

    # Sayacı doğrudan manipüle ederek limiti doldur.
    import time

    uid = None
    # Kullanıcı id'sini bulmak için iç veriyi kullanıyoruz (hits'te tek key var).
    hits = limiter._hits
    uid = next(iter(hits))  # tek kullanıcı var
    limit = limiter.limit
    # Pencere içinde limit kadar sahte hit ekle (gerçek isteği de saydığımız için limit-1).
    now = time.monotonic()
    hits[uid].extend([now] * (limit - len(hits[uid])))

    # Bir daha istek at → 429.
    r2 = await client.get(
        f"/v1/vehicles/{vid}/tasks/oil_change/guide", headers=headers
    )
    assert r2.status_code == 429


# =========================================================================== #
# 429 — rate limit (summary endpoint)
# =========================================================================== #


@pytest.mark.asyncio
async def test_summary_rate_limit_429(client):
    """Rate limiti doldurulunca summary endpoint 429 döner."""
    from app.core.rate_limit import get_rate_limiter

    import time

    headers = await register_and_login(client, "sum_rl@usta.app")
    vehicle = await create_vehicle(client, headers)
    vid = vehicle["id"]
    limiter = get_rate_limiter()

    limiter.reset()
    # İlk istek geçmeli.
    r = await client.get(f"/v1/vehicles/{vid}/summary", headers=headers)
    assert r.status_code == 200

    hits = limiter._hits
    uid = next(iter(hits))
    now = time.monotonic()
    hits[uid].extend([now] * (limiter.limit - len(hits[uid])))

    r2 = await client.get(f"/v1/vehicles/{vid}/summary", headers=headers)
    assert r2.status_code == 429
