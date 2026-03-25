-- PostgreSQL inicijalni skript za servo bazu
-- Autor: AI Assistant

-- Kreiranje ekstenzije za timestamp sa timezone
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Optimizacija za servo_movements tabelu
CREATE INDEX IF NOT EXISTS idx_servo_movements_timestamp_desc 
ON servo_movements (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_servo_movements_angle 
ON servo_movements (angle);

CREATE INDEX IF NOT EXISTS idx_servo_movements_success 
ON servo_movements (success);

-- Kreiranje particije za bolje performanse (opciono za velike baze)
-- Ovo može se dodati kasnije ako bude potrebno
/*
CREATE TABLE servo_movements_y2024m01 PARTITION OF servo_movements
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
*/

-- Grantovanje prava korisniku
GRANT ALL PRIVILEGES ON DATABASE servo_db TO postgres;
