from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    bot_token: str
    admin_id: int
    db_path: str = "data/reservations.db"
    slot_duration_minutes: int = 60
    day_start_hour: int = 8
    day_end_hour: int = 21
    max_advance_days: int = 14
