import time
from src.utils.logger import get_logger
from src.etl.extract import extract_all
from src.etl.transform import (
    clean_and_build_dimensions,
    build_fact_socioeconomic,
    build_fact_mental_health
)
from src.etl.load import load_all_to_files, load_to_database

logger = get_logger("MAIN_PIPELINE")

def run_pipeline():
    start_time = time.time()
    logger.info(">>> BAT DAU PIPELINE ETL KHO DU LIEU TAM THAN (IS217) <<<")
    
    # 1. Extract
    raw_data = extract_all()
    
    # 2. Transform
    dim_loc, dim_t, dim_c, dim_d, loc_map, cause_map, demo_map = clean_and_build_dimensions(
        raw_data["quocgia"], raw_data["gbd"]
    )
    fact_se = build_fact_socioeconomic(raw_data["kinhtexahoi"], loc_map)
    fact_mh = build_fact_mental_health(raw_data["gbd"], loc_map, cause_map, demo_map)
    
    dims = {
        "dim_location": dim_loc,
        "dim_time": dim_t,
        "dim_cause": dim_c,
        "dim_demographic": dim_d
    }
    facts = {
        "fact_socioeconomic": fact_se,
        "fact_mental_health": fact_mh
    }
    
    # 3. Load
    load_all_to_files(dims, facts)
    load_to_database(dims, facts)
    
    elapsed = time.time() - start_time
    logger.info(f">>> HOAN THANH PIPELINE TRONG {elapsed:.2f} GIAY! <<<")

if __name__ == "__main__":
    run_pipeline()
