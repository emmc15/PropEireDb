\c propeiredb;
CREATE TABLE IF NOT EXISTS "propeiredb".geo_encoding_lookup (
    address_hash TEXT PRIMARY KEY,
    input_address TEXT,
    output_address TEXT,
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    region TEXT
)