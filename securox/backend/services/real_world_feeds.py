"""
Securox — Real-World Data Feed Service
Polls real public APIs and converts live data into structured risk events
that feed directly into the existing ML/risk pipeline.

Sectors covered:
  ⚡ Power Grid      → Open-Meteo (temperature, cloud cover)
  💧 Water Supply    → Open-Meteo (precipitation, humidity)
  🏥 Healthcare      → Open-Meteo (UV index, heat stress) + WHO RSS
  🚦 Traffic System  → Camera AI (handled separately in main.py)
  📡 Communications  → HTTP latency checks (real network round-trip)
  🏦 Finance         → CoinGecko free API (BTC/ETH 24h change)
  🚨 Emergency Svcs  → Open-Meteo (wind speed, weather code → storm/flood)
  🚌 Public Transit  → Time-of-day rush-hour rules + weather delay factor
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("securox.real_world_feeds")

# ── Config ────────────────────────────────────────────────────────────────────
# Default to Bengaluru, India — change lat/lon for your city
LATITUDE  = 12.9716
LONGITUDE = 77.5946
CITY_NAME = "Bengaluru"

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LATITUDE}&longitude={LONGITUDE}"
    "&current=temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,uv_index,cloud_cover,weather_code"
    "&timezone=auto"
)

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,binancecoin"
    "&vs_currencies=usd"
    "&include_24hr_change=true"
)

# Public endpoints used for latency checks (no data sent)
LATENCY_TARGETS = [
    ("Google DNS",    "https://dns.google"),
    ("Cloudflare",    "https://1.1.1.1"),
    ("OpenDNS",       "https://www.opendns.com"),
]

WHO_RSS_URL = "https://www.who.int/rss-feeds/news-releases.xml"

POLL_INTERVAL_SECONDS = 45  # how often each feed cycle runs


# ── WMO Weather Code → Description ────────────────────────────────────────────
WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight showers", 81: "Moderate showers",
    82: "Violent showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm + hail", 99: "Thunderstorm + heavy hail",
}

SEVERE_WEATHER_CODES = {45, 48, 65, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}


class RealWorldFeedService:
    """
    Background service that fetches live data from public APIs and
    converts it into Securox risk events / digital twin updates.
    """

    def __init__(self):
        self._running      = False
        self._last_weather: dict = {}
        self._last_finance: dict = {}
        self._last_latency: dict = {}
        self._last_who_alert: str = ""
        self.feed_status: dict[str, Any] = {}   # visible at /api/real-world/status
        self._callbacks: list = []              # list of async callables

    def on_event(self, callback):
        """Register an async callback to receive (asset, risk_score, metadata) tuples."""
        self._callbacks.append(callback)

    async def _emit(self, asset: str, risk_score: float, metadata: dict):
        for cb in self._callbacks:
            try:
                await cb(asset, risk_score, metadata)
            except Exception as e:
                logger.warning("Feed callback error: %s", e)

    # ── Main loop ─────────────────────────────────────────────────────────────
    async def start(self):
        self._running = True
        logger.info("Real-world feed service started (city: %s)", CITY_NAME)
        while self._running:
            try:
                await self._cycle()
            except Exception as exc:
                logger.warning("Feed cycle error: %s", exc)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def stop(self):
        self._running = False

    async def _cycle(self):
        """Run all feed polls concurrently once."""
        results = await asyncio.gather(
            self._poll_weather(),
            self._poll_finance(),
            self._poll_latency(),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.debug("Feed gather error: %s", r)

    # ── Weather → Power, Water, Healthcare, Emergency, Transit ───────────────
    async def _poll_weather(self):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(OPEN_METEO_URL)
            resp.raise_for_status()
            data = resp.json()

        cur = data.get("current", {})
        temp        = cur.get("temperature_2m", 25)       # °C
        humidity    = cur.get("relative_humidity_2m", 60) # %
        precip      = cur.get("precipitation", 0)         # mm
        wind_speed  = cur.get("wind_speed_10m", 10)       # km/h
        uv_index    = cur.get("uv_index", 3)
        cloud_cover = cur.get("cloud_cover", 30)          # %
        wx_code     = int(cur.get("weather_code", 0))
        wx_desc     = WMO_CODES.get(wx_code, "Unknown")
        is_severe   = wx_code in SEVERE_WEATHER_CODES

        self._last_weather = {
            "temperature": temp, "humidity": humidity,
            "precipitation": precip, "wind_speed": wind_speed,
            "uv_index": uv_index, "cloud_cover": cloud_cover,
            "weather_code": wx_code, "weather_desc": wx_desc,
            "is_severe": is_severe, "city": CITY_NAME,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # ── Power Grid risk ──────────────────────────────────────────────────
        # High heat → AC load spikes; extreme cold → heating spike
        heat_stress  = max(0, temp - 35) * 4     # +4 risk per degree above 35°C
        cold_stress  = max(0, 5 - temp) * 3      # +3 risk per degree below 5°C
        cloud_factor = (100 - cloud_cover) / 100  # solar panels less effective with clouds
        power_risk   = min(100, 12 + heat_stress + cold_stress + (20 if is_severe else 0))
        await self._emit("power_grid", power_risk, {
            "source":  "Open-Meteo Weather",
            "asset":   "power_grid",
            "reason":  f"Temperature {temp}°C, wind {wind_speed}km/h, {wx_desc}",
            "raw":     {"temperature": temp, "wind_speed": wind_speed, "weather": wx_desc},
        })

        # ── Water Supply risk ────────────────────────────────────────────────
        # Heavy rain → flooding/contamination; drought (no precip) → shortage
        flood_risk   = min(50, precip * 8)        # heavy rain → contamination
        drought_risk = max(0, 10 - precip * 5)    # low precip → shortage pressure
        water_risk   = min(100, 8 + flood_risk + drought_risk + (15 if is_severe else 0))
        await self._emit("water_supply", water_risk, {
            "source": "Open-Meteo Precipitation",
            "asset":  "water_supply",
            "reason": f"Precipitation {precip}mm, humidity {humidity}%, {wx_desc}",
            "raw":    {"precipitation": precip, "humidity": humidity},
        })

        # ── Healthcare risk ──────────────────────────────────────────────────
        # UV + heat stress → illness surge; severe weather → trauma cases
        heat_health  = max(0, temp - 38) * 5
        uv_health    = max(0, uv_index - 7) * 3
        health_risk  = min(100, 10 + heat_health + uv_health + (20 if is_severe else 0))
        await self._emit("healthcare", health_risk, {
            "source": "Open-Meteo UV/Temperature",
            "asset":  "healthcare",
            "reason": f"UV index {uv_index}, temperature {temp}°C, {wx_desc}",
            "raw":    {"uv_index": uv_index, "temperature": temp},
        })

        # ── Emergency Services risk ──────────────────────────────────────────
        # Storms, high winds, flooding → emergency call surges
        wind_risk    = min(40, max(0, wind_speed - 40) * 1.5)  # above 40km/h
        severe_bonus = 35 if is_severe else 0
        precip_bonus = min(20, precip * 4)
        emerg_risk   = min(100, 8 + wind_risk + severe_bonus + precip_bonus)
        await self._emit("emergency_svcs", emerg_risk, {
            "source": "Open-Meteo Severe Weather",
            "asset":  "emergency_svcs",
            "reason": f"Wind {wind_speed}km/h, {wx_desc}, precipitation {precip}mm",
            "raw":    {"wind_speed": wind_speed, "weather_code": wx_code},
        })

        # ── Public Transit risk ──────────────────────────────────────────────
        hour         = datetime.now().hour
        is_rush      = (7 <= hour <= 9) or (17 <= hour <= 19)
        rush_bonus   = 25 if is_rush else 0
        weather_delay= min(30, precip * 5 + (wind_speed - 30) * 0.5 if wind_speed > 30 else precip * 5)
        transit_risk = min(100, 10 + rush_bonus + weather_delay + (10 if is_severe else 0))
        await self._emit("public_transit", transit_risk, {
            "source": "Open-Meteo + Time-of-Day Rules",
            "asset":  "public_transit",
            "reason": (
                f"{'Rush hour, ' if is_rush else ''}"
                f"precipitation {precip}mm, wind {wind_speed}km/h"
            ),
            "raw":    {"is_rush_hour": is_rush, "precipitation": precip},
        })

        self.feed_status["weather"] = {
            "status": "ok",
            "city":   CITY_NAME,
            "temperature": f"{temp}°C",
            "condition":   wx_desc,
            "updated_at":  self._last_weather["updated_at"],
        }
        logger.info("Weather feed OK: %s °C, %s", temp, wx_desc)

    # ── Finance → Financial Network ────────────────────────────────────────────
    async def _poll_finance(self):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(COINGECKO_URL)
            resp.raise_for_status()
            data = resp.json()

        btc_change  = abs(data.get("bitcoin",      {}).get("usd_24h_change", 0))
        eth_change  = abs(data.get("ethereum",     {}).get("usd_24h_change", 0))
        bnb_change  = abs(data.get("binancecoin",  {}).get("usd_24h_change", 0))
        btc_price   = data.get("bitcoin",      {}).get("usd", 0)
        eth_price   = data.get("ethereum",     {}).get("usd", 0)

        # Volatility spikes signal financial network stress
        avg_vol     = (btc_change + eth_change + bnb_change) / 3
        fin_risk    = min(100, 8 + avg_vol * 3.5)   # 10% change → ~43 risk

        self._last_finance = {
            "btc_price": btc_price, "eth_price": eth_price,
            "btc_24h_change": round(btc_change, 2),
            "eth_24h_change": round(eth_change, 2),
            "avg_volatility": round(avg_vol, 2),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._emit("finance", fin_risk, {
            "source": "CoinGecko Market Data",
            "asset":  "finance",
            "reason": (
                f"BTC ${btc_price:,.0f} ({btc_change:+.1f}%), "
                f"ETH ${eth_price:,.0f} ({eth_change:+.1f}%)"
            ),
            "raw":    self._last_finance,
        })

        self.feed_status["finance"] = {
            "status":         "ok",
            "btc_price":      f"${btc_price:,.0f}",
            "btc_24h_change": f"{data.get('bitcoin',{}).get('usd_24h_change',0):+.2f}%",
            "eth_price":      f"${eth_price:,.0f}",
            "updated_at":     self._last_finance["updated_at"],
        }
        logger.info("Finance feed OK: BTC $%s, vol %.1f%%", btc_price, avg_vol)

    # ── Communications → Latency health ───────────────────────────────────────
    async def _poll_latency(self):
        results = []
        async with httpx.AsyncClient(timeout=6) as client:
            for name, url in LATENCY_TARGETS:
                t0 = time.monotonic()
                try:
                    await client.head(url, follow_redirects=True)
                    latency_ms = (time.monotonic() - t0) * 1000
                    results.append({"name": name, "latency_ms": round(latency_ms, 1), "ok": True})
                except Exception:
                    results.append({"name": name, "latency_ms": 9999, "ok": False})

        # Risk = function of average latency
        avg_latency = sum(r["latency_ms"] for r in results) / len(results)
        failed      = sum(1 for r in results if not r["ok"])
        comms_risk  = min(100, 5 + avg_latency * 0.05 + failed * 25)

        self._last_latency = {
            "targets":    results,
            "avg_ms":     round(avg_latency, 1),
            "failed":     failed,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._emit("communications", comms_risk, {
            "source": "Live HTTP Latency Checks",
            "asset":  "communications",
            "reason": (
                f"Avg latency {avg_latency:.0f}ms across "
                f"{len(LATENCY_TARGETS)} endpoints, {failed} unreachable"
            ),
            "raw":    self._last_latency,
        })

        self.feed_status["communications"] = {
            "status":     "ok" if failed == 0 else "degraded",
            "avg_ms":     f"{avg_latency:.0f}ms",
            "failed":     failed,
            "targets":    [r["name"] for r in results],
            "updated_at": self._last_latency["updated_at"],
        }
        logger.info("Comms feed OK: avg latency %.0fms, %d failed", avg_latency, failed)


# ── singleton ─────────────────────────────────────────────────────────────────
real_world_feeds = RealWorldFeedService()
