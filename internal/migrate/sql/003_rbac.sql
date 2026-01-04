-- RBAC and attestation authorities
CREATE TABLE IF NOT EXISTS actors(
  id TEXT PRIMARY KEY,
  display_name TEXT,
  kind TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles(
  id TEXT PRIMARY KEY,
  description TEXT
);

CREATE TABLE IF NOT EXISTS permissions(
  id TEXT PRIMARY KEY,
  description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions(
  role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id TEXT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY(role_id, permission_id)
);
CREATE INDEX IF NOT EXISTS idx_role_perms_role ON role_permissions(role_id);

CREATE TABLE IF NOT EXISTS actor_roles(
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  actor_id TEXT NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
  role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY(project_id, actor_id, role_id)
);
CREATE INDEX IF NOT EXISTS idx_actor_roles_actor ON actor_roles(project_id, actor_id);

CREATE TABLE IF NOT EXISTS attestation_authorities(
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY(project_id, kind, role_id)
);
CREATE INDEX IF NOT EXISTS idx_att_auth_kind ON attestation_authorities(project_id, kind);

-- Expand events entity_kind to include rbac
PRAGMA foreign_keys=off;
ALTER TABLE events RENAME TO events_old;
CREATE TABLE events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  project_id TEXT,
  entity_kind TEXT CHECK(entity_kind IN ('project','iteration','task','decision','lease','attestation','rbac')) NOT NULL,
  entity_id TEXT,
  actor_id TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
INSERT INTO events(id, ts, type, project_id, entity_kind, entity_id, actor_id, payload_json)
SELECT id, ts, type, project_id, entity_kind, entity_id, actor_id, payload_json FROM events_old;
DROP TABLE events_old;
PRAGMA foreign_keys=on;
