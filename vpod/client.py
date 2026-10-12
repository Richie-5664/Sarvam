import os
import sys
from pathlib import Path
from sarvamai import SarvamAI

# Ensure UTF-8 output encoding for console displays
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env() -> None:
    """Load variables from .env into os.environ without overriding existing ones."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    val = value.strip().strip("'\"")
                    if key and not os.environ.get(key):
                        os.environ[key] = val


def get_sarvam_client() -> SarvamAI:
    """Initialize and return an authenticated SarvamAI client."""
    load_env()
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError(
            "SARVAM_API_KEY is not set. Please add it to your .env file or environment."
        )
    return SarvamAI(api_subscription_key=api_key)
