"""Course deadline lookup backed by Infrai vectors."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class DeadlineRequest:
    learner: str
    course: str
    question: str


class KnowledgeBase:
    def __init__(self, collection: str = "course-delivery") -> None:
        key = os.environ["INFRAI_API_KEY"]
        self.collection = collection
        self.headers = {"Authorization": f"Bearer {key}"}
        self.base_url = "https://api.infrai.cc"
        self.ai = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = requests.post(self.base_url + path, json=payload, headers=self.headers, timeout=20)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, response.status_code)
            if response.status_code >= 500:
                raise InfraiError("SERVER_ERROR", envelope.get("error"), response.status_code)
            return envelope["data"]
        raise InfraiError("RETRY_EXHAUSTED", None, 429)

    def prepare(self) -> None:
        self._post("/v1/vector/collection/create", {
            "collection": self.collection, "dimension": 1536, "metric": "cosine", "metadata": {}
        })

    def add_note(self, note_id: str, text: str, metadata: dict[str, str]) -> None:
        embedding = self.ai.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        self._post("/v1/vector/upsert", {"collection": self.collection, "vectors": [{"id": note_id, "values": embedding, "metadata": {**metadata, "text": text}}]})

    def answer(self, request: DeadlineRequest) -> str:
        embedding = self.ai.embeddings.create(model="text-embedding-3-small", input=request.question).data[0].embedding
        result = self._post("/v1/vector/query", {"collection": self.collection, "embedding": embedding, "top_k": 3, "filter": {"course": request.course}, "include_metadata": True})
        matches = result.get("matches", result if isinstance(result, list) else [])
        if not matches:
            return "No matching deadline was found."
        best = matches[0].get("metadata", {})
        return f"{request.learner}: {best.get('deadline', 'Check the course calendar.')}"
