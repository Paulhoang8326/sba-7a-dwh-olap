-- ====================================================================
-- OLAP Operation 2: Slice & Dice
-- ====================================================================

-- 2.1 Slice: Cat lat du lieu duy nhat cho nam 2021 (giai doan COVID-19) tren tat ca cac quoc gia
SELECT 
    loc.location_name,
    c.cause_name,
    d.sex_name,
    f.prevalence_number,
    f.dalys_number
FROM dwh.fact_mental_health f
JOIN dwh.dim_location loc ON f.location_key = loc.location_key
JOIN dwh.dim_time t ON f.time_key = t.time_key
JOIN dwh.dim_cause c ON f.cause_key = c.cause_key
JOIN dwh.dim_demographic d ON f.demographic_key = d.demographic_key
WHERE t.year = 2021
  AND c.is_overall_total = TRUE
ORDER BY f.dalys_number DESC
LIMIT 20;

-- 2.2 Dice: Xuc xac da chieu: Chi xet (Nam: 2019, 2021) AND (Gioi tinh: Female) AND (Benh: Depressive disorders) AND (Nhom thu nhap: High vs Low)
SELECT 
    t.year,
    loc.income_group,
    ROUND(AVG(f.prevalence_percent * 100), 3) AS avg_female_depression_pct,
    ROUND(SUM(f.dalys_number), 0) AS total_female_depression_dalys
FROM dwh.fact_mental_health f
JOIN dwh.dim_location loc ON f.location_key = loc.location_key
JOIN dwh.dim_time t ON f.time_key = t.time_key
JOIN dwh.dim_cause c ON f.cause_key = c.cause_key
JOIN dwh.dim_demographic d ON f.demographic_key = d.demographic_key
WHERE t.year IN (2019, 2021)
  AND d.sex_name = 'Female'
  AND c.cause_name = 'Depressive disorders'
  AND loc.income_group IN ('High income', 'Low income')
GROUP BY t.year, loc.income_group
ORDER BY t.year, loc.income_group;
