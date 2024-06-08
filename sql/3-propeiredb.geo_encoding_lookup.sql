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
    address_hash,
    address,
    sale_date,
    county,
    province,
    postal_code
from propeiredb.residential_register
inner join propeiredb.geo_encoding_lookup on propeiredb.residential_register.address_hash = propeiredb.geo_encoding_lookup.address_hash
where lat is null or lon is null;