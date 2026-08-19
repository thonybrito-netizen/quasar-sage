import json


def test_visionary_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Your draft leads with the edge-node spec sheet, not the belief behind it.",
            "generated_content": "We believe industrial edge networks should never experience unplanned downtime.",
            "suggested_next_action": "advance_to_storyteller",
            "sourced_fields": {"industry": "industry"},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer qn-test-key"},
        json={
            "module": "visionary",
            "user_message": "Help me position our new IIoT gateway.",
            "context": {"industry": "IIoT", "enemy": "unplanned downtime"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "visionary"
    assert body["resolved_via"] == "first_attempt"
    assert "downtime" in body["generated_content"]


def test_missing_auth_header_is_rejected(client, fake_claude):
    fake_claude([])
    response = client.post(
        "/v1/completions",
        json={"module": "visionary", "user_message": "hi", "context": {}},
    )
    assert response.status_code in (401, 422)


def test_wrong_api_key_is_rejected(client, fake_claude):
    fake_claude([])
    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer not-a-real-key"},
        json={"module": "visionary", "user_message": "hi", "context": {}},
    )
    assert response.status_code == 401
