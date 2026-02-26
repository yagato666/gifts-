import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    admins_chat_id: int
    channels: list[str]
    admins: list[int]


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Put it into .env")

    admins_chat_id_raw = os.getenv("ADMINS_CHAT_ID", "").strip()
    if not admins_chat_id_raw:
        raise RuntimeError("ADMINS_CHAT_ID is empty. Put it into .env")
    admins_chat_id = int(admins_chat_id_raw)

    channels_raw = os.getenv("CHANNELS", "").strip()
    channels = [c.strip() for c in channels_raw.split(",") if c.strip()]
    if not channels:
        raise RuntimeError("CHANNELS is empty. Example: @channel1,@channel2")

    admins_raw = os.getenv("ADMINS", "").strip()
    if not admins_raw:
        raise RuntimeError("ADMINS is empty. Example: ADMINS=123456789,987654321")

    admins = [int(x.strip()) for x in admins_raw.split(",") if x.strip().isdigit()]
    if not admins:
        raise RuntimeError("ADMINS parsing error. Example: ADMINS=123456789")

    return Config(
        bot_token=bot_token,
        admins_chat_id=admins_chat_id,
        channels=channels,
        admins=admins,
    )


GIFTS = {
    "bear": {"name": "🧸 Мишка", "price": 4},
    "rose": {"name": "🌹 Роза", "price": 6},
    "rocket": {"name": "🚀 Ракета", "price": 10},
    "diamond": {"name": "💎 Алмаз", "price": 16},
}
