-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE cities (
  id        SERIAL PRIMARY KEY,
  slug      TEXT UNIQUE NOT NULL,
  name      TEXT NOT NULL,
  uf        CHAR(2) NOT NULL,
  active    BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
  id               BIGSERIAL PRIMARY KEY,
  city_id          INTEGER NOT NULL REFERENCES cities(id),
  address          TEXT NOT NULL,
  neighborhood     TEXT,
  zip_code         TEXT,
  value            NUMERIC(14, 2) NOT NULL,
  area_m2          NUMERIC(8, 2),
  price_m2         NUMERIC(10, 2) GENERATED ALWAYS AS (
                     CASE WHEN area_m2 > 0 THEN ROUND(value / area_m2, 2) ELSE NULL END
                   ) STORED,
  property_type    TEXT CHECK (property_type IN ('residential', 'commercial', 'land')),
  transaction_date DATE NOT NULL,
  source           TEXT NOT NULL,
  external_id      TEXT,
  geom             GEOMETRY(POINT, 4326),
  raw_data         JSONB,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (source, external_id)
);

-- Neighborhood aggregate cache
CREATE TABLE neighborhood_stats (
  id                BIGSERIAL PRIMARY KEY,
  city_id           INTEGER NOT NULL REFERENCES cities(id),
  neighborhood      TEXT NOT NULL,
  avg_price_m2      NUMERIC(10, 2),
  transaction_count INTEGER,
  period_start      DATE,
  period_end        DATE,
  updated_at        TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (city_id, neighborhood)
);

-- Indexes
CREATE INDEX idx_transactions_geom     ON transactions USING GIST(geom);
CREATE INDEX idx_transactions_city     ON transactions(city_id);
CREATE INDEX idx_transactions_date     ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_hood     ON transactions(neighborhood);
CREATE INDEX idx_transactions_source   ON transactions(source, external_id);

-- Seed cities
INSERT INTO cities (slug, name, uf) VALUES
  ('sao-paulo',      'São Paulo',       'SP'),
  ('rio-de-janeiro', 'Rio de Janeiro',  'RJ'),
  ('belo-horizonte', 'Belo Horizonte',  'MG'),
  ('porto-alegre',   'Porto Alegre',    'RS');

-- Row Level Security: read is public
ALTER TABLE transactions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE neighborhood_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE cities             ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read transactions"
  ON transactions FOR SELECT USING (true);

CREATE POLICY "public read neighborhood_stats"
  ON neighborhood_stats FOR SELECT USING (true);

CREATE POLICY "public read cities"
  ON cities FOR SELECT USING (true);
