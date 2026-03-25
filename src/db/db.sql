CREATE TABLE IF NOT EXISTS PURGE_INFO(
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS airports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    iata VARCHAR(8),
    icao VARCHAR(8),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    search BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_airports_iata UNIQUE (iata),
    CONSTRAINT uq_airports_icao UNIQUE (icao)
);

CREATE TABLE IF NOT EXISTS flights (
    id SERIAL PRIMARY KEY,
    id_flight VARCHAR(10),
    number VARCHAR(16),
    origin_airport_id INTEGER,
    destination_airport_id INTEGER,
    scheduled_departure VARCHAR(40),
    utc_departure BIGINT,
    scheduled_arrival VARCHAR(40),
    utc_arrival BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_flights_id_flight UNIQUE (id_flight),
    CONSTRAINT chk_id_flight_len CHECK (id_flight IS NULL OR char_length(id_flight) BETWEEN 8 AND 10),
    CONSTRAINT chk_number_len CHECK (number IS NULL OR char_length(number) BETWEEN 1 AND 16),
    CONSTRAINT fk_flights_origin_airport
        FOREIGN KEY (origin_airport_id)
        REFERENCES airports (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_flights_destination_airport
        FOREIGN KEY (destination_airport_id)
        REFERENCES airports (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_flights_origin_airport_id ON flights (origin_airport_id);
CREATE INDEX IF NOT EXISTS idx_flights_destination_airport_id ON flights (destination_airport_id);
CREATE INDEX IF NOT EXISTS idx_flights_utc_departure ON flights (utc_departure);
CREATE INDEX IF NOT EXISTS idx_flights_utc_arrival ON flights (utc_arrival);