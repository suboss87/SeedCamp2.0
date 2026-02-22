from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # API
    ark_api_key: str = ""
    ark_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"

    # --- Model IDs ---
    # Seed 1.8: script generation + video review
    script_model: str = "seed-1-8-251228"
    # Seedance 1.5 Pro: hero SKU video (top 20%, cinematic quality)
    video_model_pro: str = "seedance-1-5-pro-251215"
    # Seedance 1.0 Pro Fast: catalog SKU video (80%, cost-optimized)
    video_model_fast: str = "seedance-1-0-pro-fast-251015"

    # --- Cost per million tokens (USD) ---
    cost_per_m_seed18_input: float = 0.25
    cost_per_m_seed18_output: float = 2.00
    cost_per_m_seedance_pro: float = 1.20
    cost_per_m_seedance_fast: float = 0.70

    # --- Video defaults ---
    video_duration: int = 8  # seconds (2-12)
    video_resolution: str = "720p"
    video_sound: bool = True
    poll_interval: int = 5
    poll_timeout: int = 300

    # --- Batch / Brief generation ---
    batch_concurrency_default: int = 3
    brief_temperature: float = 0.8
    brief_max_tokens: int = 256

    # --- Security ---
    cors_origins: str = (
        "*"  # Comma-separated origins, e.g. "https://example.com,https://app.example.com"
    )
    api_key: str = ""  # Optional API key to protect endpoints; leave empty to disable
    rate_limit: str = "60/minute"  # Rate limit per client (slowapi format)
    max_upload_size_mb: int = 10  # Max image upload size in MB

    # --- Storage ---
    output_dir: Path = Path("output")
    gcs_bucket: str = "your-gcs-bucket-name"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
