\c propeiredb;
CREATE OR REPLACE VIEW propeiredb.residential_register_dublin_mapped AS
SELECT joined.*
FROM (
        SELECT local.*,
            mapped.output_address,
            mapped.lat,
            mapped.lon,
            mapped.region
        FROM (
                SELECT *
                FROM propeiredb.residential_register
                WHERE county = 'Dublin'
            ) as local
            INNER JOIN propeiredb.geo_encoding_lookup as mapped ON local.address_hash = mapped.address_hash
    ) as joined;
CREATE OR REPLACE VIEW propeiredb.residential_register_dublin_unmapped AS
SELECT local.address,
    local.address_hash,
    local.sale_date
FROM (
        SELECT *
        FROM propeiredb.residential_register
        WHERE county = 'Dublin'
    ) as local
    LEFT JOIN propeiredb.geo_encoding_lookup as mapped ON local.address_hash = mapped.address_hash
WHERE mapped.address_hash is null;