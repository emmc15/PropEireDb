\c property_register;
CREATE TABLE IF NOT EXISTS "propeiredb".geo_encoding_lookup (
    address_hash TEXT PRIMARY KEY,
    input_address TEXT,
    output_address TEXT,
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    region TEXT
);


CREATE OR REPLACE view propeiredb.missing_geo_encoded_addresses as 
select 
    rr.address_hash,
    address,
    sale_date,
    county,
    province,
    postal_code
from propeiredb.residential_register as rr
left join propeiredb.geo_encoding_lookup as lookup
on rr.address_hash = lookup.address_hash
where lookup.address_hash is null;

