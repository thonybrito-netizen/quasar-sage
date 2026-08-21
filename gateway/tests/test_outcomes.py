def test_record_outcome_accepted(client, fake_outcome_store):
    response = client.post(
        "/v1/outcomes",
        headers={"Authorization": "Bearer qn-test-key"},
        json={"module": "storyteller", "field_type": "opening_hook", "label": "accepted"},
    )
    assert response.status_code == 204
    assert fake_outcome_store == [
        {"tenant_id": "quietnoise", "module": "storyteller", "mode": None, "field_type": "opening_hook", "label": "accepted"}
    ]


def test_record_outcome_rejected_with_mode(client, fake_outcome_store):
    response = client.post(
        "/v1/outcomes",
        headers={"Authorization": "Bearer lo-test-key"},
        json={"module": "dealmaker", "mode": "enterprise", "field_type": "proposal_draft", "label": "rejected"},
    )
    assert response.status_code == 204
    assert fake_outcome_store[0]["tenant_id"] == "lorito"
    assert fake_outcome_store[0]["label"] == "rejected"


def test_record_outcome_requires_auth(client, fake_outcome_store):
    response = client.post(
        "/v1/outcomes",
        json={"module": "storyteller", "field_type": "opening_hook", "label": "accepted"},
    )
    assert response.status_code in (401, 422)
    assert fake_outcome_store == []


def test_record_outcome_rejects_invalid_label(client, fake_outcome_store):
    response = client.post(
        "/v1/outcomes",
        headers={"Authorization": "Bearer qn-test-key"},
        json={"module": "storyteller", "field_type": "opening_hook", "label": "maybe"},
    )
    assert response.status_code == 422
    assert fake_outcome_store == []


def test_record_outcome_store_failure_returns_503(client, monkeypatch, env_setup):
    from app.routers import outcomes as outcomes_module

    def _boom(*args, **kwargs):
        raise RuntimeError("Firestore unavailable")

    monkeypatch.setattr(outcomes_module, "write_outcome", _boom)

    response = client.post(
        "/v1/outcomes",
        headers={"Authorization": "Bearer qn-test-key"},
        json={"module": "storyteller", "field_type": "opening_hook", "label": "accepted"},
    )
    assert response.status_code == 503
