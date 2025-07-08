from pathlib import Path

current_file = Path(__file__).resolve()
project_root = current_file.parents[1]


class Config:
    DB_PATH = project_root / "reviews.db"

