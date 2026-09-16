"""
API-to-API automation connector.

Pulls current weather from the public Open-Meteo API and delivers a
formatted summary to Slack (if a webhook is configured) plus a local
CSV log. Stands in for the most common "connect API X to API Y" gig:
pull data on a schedule, transform it, push it somewhere the client
actually looks (Slack, email, a spreadsheet).

What this demonstrates for a client-facing gig:
  - All client-tunable values pulled from .env via config.py, not
    hardcoded -- see that file for why this matters
  - Retry-with-backoff wrapper reused across both API calls
  - Structured logging so a failed run is diagnosable from the log
    alone, without re-running the script
  - Designed to be triggered by cron / a scheduled Lambda / Windows
    Task Scheduler -- no interactive input, clean exit codes
"""

import csv
import logging
import os
import time
from datetime import datetime, timezone
from functools import wraps

import requests

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("automation")

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


def retry(max_attempts: int = 3, base_delay: float = 2.0):
    """Reusable retry-with-backoff decorator for any network call.

    Wrapping every external call in something like this is one of the
    cheapest ways to make a script feel "production-ready" to a
    client -- a single flaky request no longer kills the whole run.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as exc:
                    last_exc = exc
                    wait = base_delay * attempt
                    log.warning(
                        f"{func.__name__} failed (attempt {attempt}/"
                        f"{max_attempts}): {exc}. Retrying in {wait}s."
                    )
                    time.sleep(wait)
            log.error(f"{func.__name__} failed after {max_attempts} attempts.")
            raise last_exc

        return wrapper

    return decorator


@retry(max_attempts=3)
def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,weather_code",
    }
    response = requests.get(WEATHER_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


@retry(max_attempts=3)
def send_slack_message(webhook_url: str, text: str) -> None:
    response = requests.post(webhook_url, json={"text": text}, timeout=10)
    response.raise_for_status()


def log_to_csv(city: str, temp_c: float, wind_kph: float, filepath: str = "weather_log.csv"):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "city", "temp_c", "wind_kph"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), city, temp_c, wind_kph])


def main():
    cfg = load_config()
    log.info(f"Fetching weather for {cfg.city_name}...")

    data = fetch_weather(cfg.city_latitude, cfg.city_longitude)
    current = data.get("current", {})
    temp_c = current.get("temperature_2m")
    wind_kph = current.get("wind_speed_10m")

    summary = f"{cfg.city_name}: {temp_c}°C, wind {wind_kph} km/h"
    log.info(summary)

    log_to_csv(cfg.city_name, temp_c, wind_kph)

    if cfg.slack_webhook_url:
        send_slack_message(cfg.slack_webhook_url, f"Daily weather update -- {summary}")
        log.info("Slack notification sent.")
    else:
        log.info("No Slack webhook configured -- skipping notification, CSV log only.")


if __name__ == "__main__":
    main()
