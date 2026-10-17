-- Giclee collections (feature/add-giclee-collections)
-- These tables are created automatically by Base.metadata.create_all on app startup.
-- This script is a manual fallback only, safe to re-run. It does not modify any existing tables.
-- Back up kelvin.db first:  cp kelvin.db kelvin-backup-$(date +%F).db
-- Run with:                 sqlite3 kelvin.db < sql/giclee_collections.sql

CREATE TABLE IF NOT EXISTS giclee_collections (
	id INTEGER NOT NULL,
	title VARCHAR(256) NOT NULL,
	description VARCHAR,
	order_number INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS giclee_collection_items (
	collection_id INTEGER NOT NULL,
	painting_id INTEGER NOT NULL,
	item_order INTEGER NOT NULL,
	PRIMARY KEY (collection_id, painting_id),
	FOREIGN KEY(collection_id) REFERENCES giclee_collections (id),
	FOREIGN KEY(painting_id) REFERENCES giclees (painting_id)
);
