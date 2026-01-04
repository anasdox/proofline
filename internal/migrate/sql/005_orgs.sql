PRAGMA foreign_keys = ON;

-- Organizations
CREATE TABLE IF NOT EXISTS organizations(
  id TEXT PRIMARY KEY,
  name TEXT,
  created_at TEXT NOT NULL
);

-- Org roles for actors
CREATE TABLE IF NOT EXISTS org_roles(
  org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  actor_id TEXT NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  PRIMARY KEY(org_id, actor_id)
);

-- Expand existing tables with org_id (default to 'default-org' for existing rows)
ALTER TABLE projects ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE iterations ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE tasks ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE decisions ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE attestations ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE events ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';
ALTER TABLE attestation_authorities ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';

-- API keys now bind to an org
ALTER TABLE api_keys ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default-org';

INSERT OR IGNORE INTO organizations(id, name, created_at) VALUES ('default-org','Default Org',strftime('%Y-%m-%dT%H:%M:%SZ','now'));
