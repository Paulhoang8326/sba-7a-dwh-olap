import csv
from pathlib import Path
from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.config import PROCESSED_DATA_PATH
from src.utils.db import get_db_engine

logger = get_logger("ETL_Load")

def save_to_csv(data: List[Dict[str, Any]], file_path: Path):
    """Luu danh sach dict thanh CSV trong processed data"""
    if not data:
        return
    file_path.parent.mkdir(parents=True, exist_ok=True)
    keys = data[0].keys()
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Da xuat file: {file_path.name} ({len(data):,} dong)")

def load_all_to_files(dims: Dict[str, List[Dict[str, Any]]], facts: Dict[str, List[Dict[str, Any]]]):
    """Xuat toan bo Dimension va Fact ra thu muc processed data phuc vu query nhanh"""
    logger.info("Dang luu du lieu vao thu muc 03_processed...")
    for name, rows in dims.items():
        save_to_csv(rows, PROCESSED_DATA_PATH / f"{name}.csv")
    for name, rows in facts.items():
        save_to_csv(rows, PROCESSED_DATA_PATH / f"{name}.csv")
    logger.info("Luu du lieu xuat khau hoan tat.")

def load_to_database(dims: Dict[str, Any], facts: Dict[str, Any]):
    """Nap du lieu vao PostgreSQL DWH neu ket noi thanh cong"""
    engine = get_db_engine()
    if not engine:
        logger.info("Bo qua buoc nap DB (he thong se luu san file processed).")
        return
    # Co the su dung pandas.to_sql neu co pandas va sqlalchemy
    logger.info("Dang ket noi va nap vao Database...")
