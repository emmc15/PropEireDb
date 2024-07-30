\c property_register;
/*province level view */
create or replace view propeiredb.province_agg_data as
select province,
    year,
    period,
    sum(price)::NUMERIC(13, 2) as total_value,
    avg(price)::NUMERIC(13, 2) as avg_price,
    count(price) as num_of_sales
from propeiredb.residential_register
group by province,
    period,
    year
order by period;
/*county level view */
create or replace view propeiredb.county_agg_data as
select county,
    province,
    year,
    period,
    sum(price)::NUMERIC(13, 2) as total_value,
    avg(price)::NUMERIC(13, 2) as avg_price,
    count(price) as num_of_sales
from propeiredb.residential_register
group by county,
    province,
    period,
    year
order by period;
create or replace view propeiredb.region_agg_data as
select region,
    year,
    period,
    sum(price)::NUMERIC(13, 2) as total_value,
    avg(price)::NUMERIC(13, 2) as avg_price,
    count(price) as num_of_sales
from propeiredb.residential_register_dublin_mapped
group by region,
    period,
    year
order by period;