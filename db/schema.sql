CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS incidents (
    eventid TEXT PRIMARY KEY,
    iyear INTEGER NOT NULL,
    imonth INTEGER,
    iday INTEGER,
    incident_date DATE,
    year_month TEXT,
    country_txt TEXT,
    region_txt TEXT,
    provstate TEXT,
    city TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    attacktype1_txt TEXT,
    targtype1_txt TEXT,
    weaptype1_txt TEXT,
    gname TEXT,
    success INTEGER,
    suicide INTEGER,
    nkill DOUBLE PRECISION,
    nwound DOUBLE PRECISION,
    casualties DOUBLE PRECISION,
    severity TEXT,
    valid_coordinates BOOLEAN,
    geo_precision TEXT,
    aggregate_only BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_incidents_year ON incidents (iyear);
CREATE INDEX IF NOT EXISTS idx_incidents_region ON incidents (region_txt);
CREATE INDEX IF NOT EXISTS idx_incidents_country ON incidents (country_txt);
CREATE INDEX IF NOT EXISTS idx_incidents_attack ON incidents (attacktype1_txt);
CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST (geom);

CREATE OR REPLACE VIEW v_region_year_trends AS
SELECT
    iyear,
    region_txt,
    COUNT(*) AS attacks,
    SUM(nkill) AS fatalities,
    SUM(nwound) AS wounded,
    SUM(casualties) AS casualties
FROM incidents
GROUP BY iyear, region_txt;

CREATE OR REPLACE VIEW v_country_hotspots AS
SELECT
    country_txt,
    COUNT(*) AS attacks,
    SUM(nkill) AS fatalities,
    SUM(nwound) AS wounded,
    AVG(latitude) AS latitude,
    AVG(longitude) AS longitude,
    TRUE AS aggregate_only
FROM incidents
WHERE valid_coordinates
GROUP BY country_txt;

