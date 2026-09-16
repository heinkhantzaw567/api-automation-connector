"""
Central config loader.

Every value a client might need to change (a webhook URL, a target
city, an API key) lives in `.env`, never hardcoded in the script
itself. This is what makes a script something a non-technical client
can hand off to someone else to tweak, or reuse for a second project,
without touching the code.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    slack_webhook_url: str
    city_latitude: float
    city_longitude: float
    city_name: str


def load_config() -> Config:
    return Config(
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        city_latitude=float(os.getenv("CITY_LATITUDE", "43.6532")),
        city_longitude=float(os.getenv("CITY_LONGITUDE", "-79.3832")),
        city_name=os.getenv("CITY_NAME", "Toronto"),
    )
