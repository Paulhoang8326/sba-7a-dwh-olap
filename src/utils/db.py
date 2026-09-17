from src.utils.logger import get_logger
from src.config import DB_URL

logger = get_logger("DB_Helper")

def get_db_engine():
    """Tra ve SQLAlchemy Engine neu co thu vien, hoac None"""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(DB_URL)
        logger.info(f"Khoi tao engine thanh cong voi DB: {DB_URL.split('@')[-1]}")
        return engine
    except ImportError:
        logger.warning("Chua cai dat SQLAlchemy hoac psycopg2. Chi ho tro xu ly file cuc bo.")
        return None
    except Exception as e:
        logger.error(f"Khong the ket noi Database: {e}")
        return None
