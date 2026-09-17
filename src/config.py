import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "01_raw"
STAGING_DATA_PATH = DATA_DIR / "02_staging"
PROCESSED_DATA_PATH = DATA_DIR / "03_processed"
SQL_DIR = BASE_DIR / "sql"

# Raw Files
FILE_QUOCGIA = RAW_DATA_PATH / "dim_quocgia.csv"
FILE_KINHTEXAHOI = RAW_DATA_PATH / "fact_kinhtexahoi.csv"
FILE_GBD = RAW_DATA_PATH / "GBD_mental_health_20-54_male_female_2013-2023.csv"
FILE_GBD_ECONOMIC = RAW_DATA_PATH / "GBD_mental_health_with_economic.csv"

# Database Configuration (from environment or defaults)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "mental_health_dwh")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
