-- ====================================================================
-- OLAP Operation 1: Roll-up & Drill-down
-- ====================================================================

-- 1.1 Roll-up: Tong hop ganh nang DALYs tu cap Quoc gia len cap Khu vuc (Region) va Nhom thu nhap (Income Group)
SELECT 
    loc.region,
    loc.income_group,
    t.year,
    c.cause_name,
    SUM(f.dalys_number) AS total_dalys_number,
    ROUND(AVG(f.prevalence_percent * 100), 3) AS avg_prevalence_pct
FROM dwh.fact_mental_health f
JOIN dwh.dim_location loc ON f.location_key = loc.location_key
JOIN dwh.dim_time t ON f.time_key = t.time_key
JOIN dwh.dim_cause c ON f.cause_key = c.cause_key
WHERE c.is_overall_total = FALSE
GROUP BY loc.region, loc.income_group, t.year, c.cause_name
ORDER BY loc.region, t.year;

-- 1.2 Drill-down: Khoan sau tu Khu vuc 'East Asia & Pacific' xuong tung Quoc gia trong nam 2023
SELECT 
    loc.location_name,
    loc.income_group,
    c.cause_name,
    f.dalys_number,
    ROUND(f.prevalence_percent * 100, 3) AS prevalence_pct
FROM dwh.fact_mental_health f
JOIN dwh.dim_location loc ON f.location_key = loc.location_key
JOIN dwh.dim_time t ON f.time_key = t.time_key
JOIN dwh.dim_cause c ON f.cause_key = c.cause_key
WHERE loc.region = 'East Asia & Pacific'
  AND t.year = 2023
  AND c.cause_name IN ('Depressive disorders', 'Anxiety disorders')
ORDER BY loc.location_name, c.cause_name;
