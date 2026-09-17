import csv
from pathlib import Path
from typing import Dict, List, Any
from src.utils.logger import get_logger
from src.config import FILE_QUOCGIA, FILE_KINHTEXAHOI, FILE_GBD

logger = get_logger("ETL_Extract")

def read_csv_as_dicts(file_path: Path) -> List[Dict[str, Any]]:
    """Doc file CSV va tra ve danh sach dictionary"""
    if not file_path.exists():
        raise FileNotFoundError(f"Khong tim thay file: {file_path}")
    logger.info(f"Bat dau doc file: {file_path.name}")
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    logger.info(f"Hoan thanh doc {file_path.name}: {len(data):,} dong")
    return data

def extract_all():
    """Trich xuat toan bo cac file raw CSV"""
    quocgia_data = read_csv_as_dicts(FILE_QUOCGIA)
    kinhtexahoi_data = read_csv_as_dicts(FILE_KINHTEXAHOI)
    gbd_data = read_csv_as_dicts(FILE_GBD)
    return {
        "quocgia": quocgia_data,
        "kinhtexahoi": kinhtexahoi_data,
        "gbd": gbd_data
    }
