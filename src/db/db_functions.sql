-- Step 1: Create (or replace) a trigger function.
-- This function runs automatically when a trigger calls it.
CREATE OR REPLACE FUNCTION purge_old_flights_by_arrival()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Step 2: Delete rows from flights where utc_arrival is below X.
    -- TG_ARGV[0] is the first argument passed from the trigger definition.
    -- We cast it to bigint because utc_arrival is numeric timestamp data.
    DELETE FROM flights
    WHERE utc_arrival IS NOT NULL
      AND utc_arrival < EXTRACT(EPOCH FROM (NOW() - INTERVAL '2 hours'))::bigint;

    -- Step 3: Return NEW as required for trigger functions.
    -- For statement-level triggers, NEW is not used, but RETURN NEW keeps function signature valid.
    RETURN NEW;
END;
$$;

-- Step 4: Drop old trigger if it already exists (prevents duplicate trigger errors).
DROP TRIGGER IF EXISTS trg_purge_old_flights_by_arrival ON flights;

-- Step 5: Create a trigger that runs after inserts or updates on flights.
-- FOR EACH STATEMENT means it runs once per SQL statement, not once per row.
CREATE TRIGGER trg_purge_old_flights_by_arrival
AFTER INSERT OR UPDATE ON flights
FOR EACH STATEMENT
EXECUTE FUNCTION purge_old_flights_by_arrival();