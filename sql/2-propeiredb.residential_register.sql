\c propeiredb;
CREATE TABLE IF NOT EXISTS "propeiredb".residential_register (
    address_hash TEXT NOT NULL,
    address TEXT NOT NULL,
    sale_date DATE NOT NULL,
    year TEXT NOT NULL,
    month TEXT NOT NULL,
    period TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    county TEXT NOT NULL,
    province TEXT NOT NULL,
    price NUMERIC NOT NULL,
    not_full_market_price TEXT,
    vat_exclusive TEXT,
    property_description TEXT,
    property_size_description TEXT,
    dublin_area_code TEXT,
    PRIMARY KEY (address_hash, sale_date)
)