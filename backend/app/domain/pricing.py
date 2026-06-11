"""Model fiyatlandırması ve teşhis başına maliyet hesabı (maliyet denetimi).

MALİYET KURALI: vision = sonnet (Opus yasak), hedef teşhis başına < $0.05.
"""

from __future__ import annotations

# USD / 1M token  ->  (girdi, çıktı)
MODEL_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

# Vision için varsayılan (bilinmeyen model -> sonnet fiyatı varsayılır).
_DEFAULT_PRICE = (3.0, 15.0)

TARGET_COST_PER_DIAGNOSIS_USD = 0.05


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    price_in, price_out = MODEL_PRICING_USD_PER_MTOK.get(model, _DEFAULT_PRICE)
    return tokens_in / 1_000_000 * price_in + tokens_out / 1_000_000 * price_out


def within_budget(model: str, tokens_in: int, tokens_out: int) -> bool:
    return cost_usd(model, tokens_in, tokens_out) <= TARGET_COST_PER_DIAGNOSIS_USD
