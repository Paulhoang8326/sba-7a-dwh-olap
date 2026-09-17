from typing import Dict, List, Any
from collections import defaultdict
from src.utils.logger import get_logger

logger = get_logger("ETL_Transform")

# Mapping danh muc nhom roi loan cho Dim_Cause
CAUSE_CATEGORY_MAP = {
    "Depressive disorders": "Mood & Affective disorders",
    "Bipolar disorder": "Mood & Affective disorders",
    "Anxiety disorders": "Neurotic & Anxiety disorders",
    "Autism spectrum disorders": "Neurodevelopmental disorders",
    "Attention-deficit/hyperactivity disorder": "Neurodevelopmental disorders",
    "Conduct disorder": "Behavioral disorders",
    "Schizophrenia": "Psychotic disorders",
    "Eating disorders": "Eating & Behavioral disorders",
    "Mental disorders": "Overall Category"
}

def clean_and_build_dimensions(quocgia_raw: List[Dict[str, Any]], gbd_raw: List[Dict[str, Any]]):
    """Xay dung cac bang Dimension va xu ly lam sach du lieu thieu"""
    logger.info("Dang xay dung cac bang Dimension...")
    
    # 1. Dim_Location
    # Xu ly 4 vung lanh tho thieu ISO/Region/Income
    dim_location = []
    location_name_to_key = {}
    for idx, row in enumerate(quocgia_raw, start=1):
        loc_name = row["location_name"].strip()
        iso3 = row["iso3"].strip() or "UNK"
        region = row["region"].strip() or "Other/Unknown"
        income = row["income_group"].strip() or "Unclassified"
        
        # Dat bien danh dac biet neu co
        if loc_name == "Taiwan":
            region = "East Asia & Pacific"
            income = "High income"
            iso3 = "TWN"
        
        dim_location.append({
            "location_key": idx,
            "location_name": loc_name,
            "iso3": iso3,
            "region": region,
            "income_group": income
        })
        location_name_to_key[loc_name] = idx
        
    # 2. Dim_Time
    years = sorted(list(set(int(float(r["year"])) for r in gbd_raw)))
    dim_time = []
    for y in years:
        phase = "Pre-COVID (2013-2019)" if y <= 2019 else ("COVID-19 Peak (2020-2021)" if y <= 2021 else "Post-COVID (2022-2023)")
        dim_time.append({
            "time_key": y,
            "year": y,
            "period_phase": phase
        })
        
    # 3. Dim_Cause
    causes_seen = {}
    dim_cause = []
    cause_idx = 1
    for r in gbd_raw:
        c_id = int(r["cause_id"])
        c_name = r["cause_name"].strip()
        if c_id not in causes_seen:
            causes_seen[c_id] = cause_idx
            dim_cause.append({
                "cause_key": cause_idx,
                "cause_id": c_id,
                "cause_name": c_name,
                "cause_category": CAUSE_CATEGORY_MAP.get(c_name, "Other"),
                "is_overall_total": (c_name == "Mental disorders")
            })
            cause_idx += 1
            
    # 4. Dim_Demographic
    dim_demographic = []
    demo_idx = 1
    demo_seen = {}
    for r in gbd_raw:
        pair = (int(r["sex_id"]), r["sex_name"].strip(), int(r["age_id"]), r["age_name"].strip())
        if pair not in demo_seen:
            demo_seen[pair] = demo_idx
            dim_demographic.append({
                "demographic_key": demo_idx,
                "sex_id": pair[0],
                "sex_name": pair[1],
                "age_id": pair[2],
                "age_name": pair[3]
            })
            demo_idx += 1
            
    logger.info(f"Tao thanh cong: {len(dim_location)} locations, {len(dim_time)} times, {len(dim_cause)} causes, {len(dim_demographic)} demographics")
    return dim_location, dim_time, dim_cause, dim_demographic, location_name_to_key, causes_seen, demo_seen

def build_fact_socioeconomic(kinhtexahoi_raw: List[Dict[str, Any]], location_name_to_key: Dict[str, int]):
    """Tao Fact_SocioEconomic tu raw data"""
    logger.info("Dang xay dung Fact_SocioEconomic...")
    fact_se = []
    idx = 1
    for r in kinhtexahoi_raw:
        loc_name = r["location_name"].strip()
        loc_key = location_name_to_key.get(loc_name)
        if not loc_key:
            continue
        year = int(float(r["year"]))
        pop = float(r["population"]) if r["population"] else None
        gdp_pc = float(r["gdp_per_capita_usd"]) if r["gdp_per_capita_usd"] else None
        gdp_tot = float(r["gdp_total_usd"]) if r["gdp_total_usd"] else None
        
        fact_se.append({
            "fact_se_id": idx,
            "location_key": loc_key,
            "time_key": year,
            "population": pop,
            "gdp_per_capita_usd": gdp_pc,
            "gdp_total_usd": gdp_tot
        })
        idx += 1
    logger.info(f"Tao thanh cong Fact_SocioEconomic: {len(fact_se):,} ban ghi")
    return fact_se

def build_fact_mental_health(gbd_raw: List[Dict[str, Any]], location_name_to_key: Dict[str, int], causes_seen: Dict[int, int], demo_seen: Dict[Any, int]):
    """Pivot va tao Fact_Mental_Health tu 161k ban ghi raw thanh ~40k ban ghi fact toi uu"""
    logger.info("Dang pivot va xay dung Fact_Mental_Health...")
    
    # Gom nhom theo (location_key, time_key, cause_key, demographic_key)
    grouped = defaultdict(dict)
    for r in gbd_raw:
        loc_name = r["location_name"].strip()
        loc_key = location_name_to_key.get(loc_name)
        time_key = int(r["year"])
        cause_key = causes_seen[int(r["cause_id"])]
        pair = (int(r["sex_id"]), r["sex_name"].strip(), int(r["age_id"]), r["age_name"].strip())
        demo_key = demo_seen[pair]
        
        composite_key = (loc_key, time_key, cause_key, demo_key)
        measure = r["measure_name"].strip() # DALYs... or Prevalence
        metric = r["metric_name"].strip()   # Number or Percent
        val = float(r["val"]) if r["val"] else None
        upper = float(r["upper"]) if r["upper"] else None
        lower = float(r["lower"]) if r["lower"] else None
        
        if "DALYs" in measure:
            if metric == "Number":
                grouped[composite_key]["dalys_number"] = val
                grouped[composite_key]["dalys_lower"] = lower
                grouped[composite_key]["dalys_upper"] = upper
            elif metric == "Percent":
                grouped[composite_key]["dalys_percent"] = val
        elif "Prevalence" in measure:
            if metric == "Number":
                grouped[composite_key]["prevalence_number"] = val
                grouped[composite_key]["prevalence_lower"] = lower
                grouped[composite_key]["prevalence_upper"] = upper
            elif metric == "Percent":
                grouped[composite_key]["prevalence_percent"] = val
                
    fact_mh = []
    fact_id = 1
    for (loc_key, time_key, cause_key, demo_key), m in grouped.items():
        fact_mh.append({
            "fact_id": fact_id,
            "location_key": loc_key,
            "time_key": time_key,
            "cause_key": cause_key,
            "demographic_key": demo_key,
            "dalys_number": m.get("dalys_number"),
            "dalys_percent": m.get("dalys_percent"),
            "dalys_lower": m.get("dalys_lower"),
            "dalys_upper": m.get("dalys_upper"),
            "prevalence_number": m.get("prevalence_number"),
            "prevalence_percent": m.get("prevalence_percent"),
            "prevalence_lower": m.get("prevalence_lower"),
            "prevalence_upper": m.get("prevalence_upper")
        })
        fact_id += 1
        
    logger.info(f"Tao thanh cong Fact_Mental_Health: {len(fact_mh):,} ban ghi da pivot")
    return fact_mh
