"""Görev kayıt defteri + GET /v1/tasks + fiyatlandırma + harness testleri."""

import pytest

from app.domain.pricing import TARGET_COST_PER_DIAGNOSIS_USD, cost_usd, within_budget
from app.domain.tasks import get_task, get_tasks
from app.services.ai.prompts import PROMPTS_DIR
from app.tools.eval_vision import offline_selfcheck

from .conftest import register_and_login


# --------------------------------------------------------------------------- #
# Kayıt defteri + prompt senkronu
# --------------------------------------------------------------------------- #


def test_every_task_has_existing_prompt_file():
    for task in get_tasks():
        assert (PROMPTS_DIR / task.prompt_file).exists(), f"prompt yok: {task.prompt_file}"


def test_get_task_lookup():
    assert get_task("battery").risk.value == "yuksek"
    assert get_task("cabin_filter").risk.value == "dusuk"
    assert get_task("olmayan") is None


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_tasks_happy(client):
    headers = await register_and_login(client, "task1@usta.app")
    r = await client.get("/v1/tasks", headers=headers)
    assert r.status_code == 200
    body = r.json()
    ids = {t["id"] for t in body}
    assert {"oil_change", "battery", "cabin_filter"} <= ids
    battery = next(t for t in body if t["id"] == "battery")
    assert battery["risk"] == "yuksek"
    assert battery["title_tr"] and battery["title_en"]


@pytest.mark.asyncio
async def test_list_tasks_requires_auth_401(client):
    r = await client.get("/v1/tasks")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Fiyatlandırma / maliyet
# --------------------------------------------------------------------------- #


def test_cost_usd_math():
    # 1M girdi @ $3, 1M çıktı @ $15
    assert cost_usd("claude-sonnet-4-5", 1_000_000, 0) == pytest.approx(3.0)
    assert cost_usd("claude-sonnet-4-5", 0, 1_000_000) == pytest.approx(15.0)


def test_typical_diagnosis_within_budget():
    # Tipik bir teşhis (1024px kare ~ 1300 girdi + 100 çıktı) bütçe içinde olmalı.
    assert within_budget("claude-sonnet-4-5", 1300, 100)
    assert cost_usd("claude-sonnet-4-5", 1300, 100) < TARGET_COST_PER_DIAGNOSIS_USD


def test_over_budget_detected():
    assert not within_budget("claude-sonnet-4-5", 20_000, 5_000)


# --------------------------------------------------------------------------- #
# Çevrimdışı harness öz-denetimi (gerçek çağrı yok)
# --------------------------------------------------------------------------- #


def test_offline_selfcheck_passes(capsys):
    rc = offline_selfcheck()
    assert rc == 0, "vision harness öz-denetimi geçmeli"
    out = capsys.readouterr().out
    assert "TÜM ÖZ-DENETİMLER GEÇTİ" in out
