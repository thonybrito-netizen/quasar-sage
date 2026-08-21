from datetime import datetime, timezone

from google.cloud import firestore

_client: firestore.Client | None = None

_COLLECTION = "sage_outcomes"


def get_firestore_client() -> firestore.Client:
    global _client
    if _client is None:
        _client = firestore.Client()
    return _client


def reset_client_for_tests() -> None:
    global _client
    _client = None


def write_outcome(tenant_id: str, module: str, mode: str | None, field_type: str, label: str) -> None:
    """Section 4.3.1: the only record Quasar's own systems persist for a
    completion -- module/Mode/field_type plus the resulting preference
    label, never the underlying draft or edit text. Firestore rather than
    Cloud SQL deliberately: this is a handful of small, schemaless
    documents with no relational needs, and it needs no VPC/private-IP
    setup on a fresh GCP project (see project memory for why that trade-
    off matters here)."""
    client = get_firestore_client()
    client.collection(_COLLECTION).add(
        {
            "tenant_id": tenant_id,
            "module": module,
            "mode": mode,
            "field_type": field_type,
            "label": label,
            "recorded_at": datetime.now(timezone.utc),
        }
    )
