import json
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    type: str
    status: str


@dataclass
class Attestation:
    id: str
    project_id: str
    entity_kind: str
    entity_id: str
    kind: str
    actor_id: str


@dataclass
class Event:
    id: int
    type: str
    project_id: str
    entity_kind: str
    entity_id: str
    actor_id: str
    payload: str


class APIError(RuntimeError):
    def __init__(self, status_code: int, body: Any):
        super().__init__(f"API error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


class ProoflineClient:
    def __init__(
        self,
        base_url: str,
        project_id: str,
        actor_id: str = "local-user",
        session: Optional[requests.Session] = None,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.actor_id = actor_id
        self.session = session or requests.Session()
        self.timeout = timeout

    def _project_path(self, suffix: str) -> str:
        return urllib.parse.urljoin(self.base_url, f"/v0/projects/{self.project_id}/{suffix}")

    def _request(self, method: str, url: str, body: Optional[Dict[str, Any]] = None):
        headers = {"Content-Type": "application/json", "X-Actor-Id": self.actor_id}
        data = json.dumps(body) if body is not None else None
        resp = self.session.request(method, url, data=data, headers=headers, timeout=self.timeout)
        if resp.status_code >= 300:
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise APIError(resp.status_code, err)
        if resp.content:
            return resp.json()
        return None

    def create_task(self, title: str, task_type: str = "feature") -> Task:
        url = self._project_path("tasks")
        data = self._request("POST", url, {"title": title, "type": task_type})
        return Task(**data)

    def add_attestation(self, entity_kind: str, entity_id: str, kind: str, payload: Any = None) -> Attestation:
        url = self._project_path("attestations")
        body = {"entity_kind": entity_kind, "entity_id": entity_id, "kind": kind}
        if payload is not None:
            body["payload"] = payload
        data = self._request("POST", url, body)
        return Attestation(**data)

    def events(self, limit: int = 20) -> List[Event]:
        url = self._project_path(f"events?limit={limit}")
        data = self._request("GET", url)
        return [Event(**item) for item in data]
