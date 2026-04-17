from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    ark_api_key: str = ""
    ark_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"

    # --- Model IDs (April 2026) ---
    # Seed 1.8: script generation + safety/quality evaluators
    script_model: str = "seed-1-8-251228"
    # Seedance 2.0 (Dreamina) — hero tier: cinematic + native audio + lip-sync
    # Ranked #2 on Artificial Analysis T2V & I2V leaderboards (April 2026),
    # ahead of Veo 3, Kling 3.0, Runway Gen-4.5.
    video_model_pro: str = "dreamina-seedance-2-0-260128"
    # Seedance 2.0 Fast — catalog tier: 720p, cost-optimized, still top-10 quality
    video_model_fast: str = "dreamina-seedance-2-0-fast-260128"

    # --- Cost per million tokens (USD) — BytePlus ModelArk, April 2026 ---
    # Source: https://docs.byteplus.com/en/docs/ModelArk/1544106
    # tokens = (in_duration_s + out_duration_s) × width × height × fps / 1024
    # Offline (async batch) mode = 50% of online rates — set video_offline=True.
    cost_per_m_seed18_input: float = 0.25
    cost_per_m_seed18_output: float = 2.00
    # Seedance 2.0 Standard: $4.30 (no-video-in, 480p/720p) → $7.70 (1080p + video-in)
    cost_per_m_seedance_pro: float = 4.30
    # Seedance 2.0 Fast: $3.30 (no-video-in) → $5.60 (with video-in). No 1080p.
    cost_per_m_seedance_fast: float = 3.30

    # --- Video defaults ---
    video_duration: int = 8  # seconds; Seedance 2.0 supports up to 15s multi-shot
    video_resolution: str = "720p"  # Seedance 2.0 Standard supports up to 1080p
    video_sound: bool = True  # Seedance 2.0 native audio (dialogue + music + foley).
    # Used by video_gen.create_video_task() and batch_generator.
    video_audio_enabled: bool = True  # Reserved for future use (e.g. separate audio
    # post-processing). Currently unused by any service — video_sound controls audio.
    video_offline: bool = False  # Async batch mode = 50% cheaper, slower turnaround
    poll_interval: int = 5
    poll_timeout: int = 300

    # --- Batch / Brief generation ---
    batch_concurrency_default: int = 3
    brief_temperature: float = 0.8
    brief_max_tokens: int = 256

    # --- Safety evaluation ---
    safety_enabled: bool = True
    safety_threshold_flag: float = 0.3  # Flag for review
    safety_threshold_high_risk: float = 0.6  # High risk — flag with warning
    safety_threshold_block: float = 0.8  # Block video generation
    safety_temperature: float = 0.0  # Deterministic evaluation
    safety_max_tokens: int = 512

    # --- Quality evaluation ---
    quality_eval_enabled: bool = True
    quality_temperature: float = 0.0  # Deterministic evaluation
    quality_max_tokens: int = 512

    # --- Regeneration ---
    max_regeneration_attempts: int = 3

    # --- Notifications ---
    notification_enabled: bool = False
    webhook_url: str = ""
    slack_webhook_url: str = ""

    # --- Dry-run mode ---
    dry_run: bool = False  # Simulate API calls without real ModelArk requests

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
    persistence_backend: str = "memory"  # "memory" (default) or "firestore"
    production: bool = False  # Set PRODUCTION=true in deployed environments

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
