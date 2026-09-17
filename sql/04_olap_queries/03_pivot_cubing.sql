-- ====================================================================
-- OLAP Operation 3: Pivot & CUBE / ROLLUP
-- ====================================================================

-- 3.1 GROUP BY CUBE da chieu giua Nhom thu nhap va Gioi tinh
SELECT 
    COALESCE(loc.income_group, 'ALL INCOMES') AS income_group,
    COALESCE(d.sex_name, 'ALL SEXES') AS sex_name,
    ROUND(AVG(f.prevalence_percent * 100), 3) AS avg_prevalence_pct,
    ROUND(SUM(f.dalys_number), 0) AS total_dalys
FROM dwh.fact_mental_health f
JOIN dwh.dim_location loc ON f.location_key = loc.location_key
JOIN dwh.dim_cause c ON f.cause_key = c.cause_key
JOIN dwh.dim_demographic d ON f.demographic_key = d.demographic_key
WHERE c.cause_name = 'Depressive disorders'
GROUP BY CUBE(loc.income_group, d.sex_name)
ORDER BY loc.income_group NULLS LAST, d.sex_name NULLS LAST;

-- 3.2 Phan tich Tuong quan lien bang Fact: GDP binh quan voi Ty le DALYs tren 100,000 dan
SELECT 
    t.year,
    loc.income_group,
    ROUND(AVG(se.gdp_per_capita_usd), 2) AS avg_gdp_per_capita,
    ROUND(SUM(mh.dalys_number) / NULLIF(SUM(se.population), 0) * 100000, 2) AS dalys_rate_per_100k
FROM dwh.fact_socioeconomic se
JOIN dwh.dim_location loc ON se.location_key = loc.location_key
JOIN dwh.dim_time t ON se.time_key = t.time_key
JOIN (
    SELECT location_key, time_key, SUM(dalys_number) AS dalys_number
    FROM dwh.fact_mental_health
    GROUP BY location_key, time_key
) mh ON se.location_key = mh.location_key AND se.time_key = mh.time_key
GROUP BY t.year, loc.income_group
ORDER BY t.year, avg_gdp_per_capita DESC;
