import json


def test_storyteller_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Draft appeals to fear of obsolescence, not just cost savings.",
            "generated_content": "Your machines were offline for 14 hours last month. What did that cost the floor?",
            "suggested_next_action": "advance_to_locker_room",
            "sourced_fields": {"downtime_hours": "downtime_hours"},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer lo-test-key"},
        json={
            "module": "storyteller",
            "user_message": "Draft a cold email about our uptime guarantee.",
            "context": {"downtime_hours": 14, "positioning": "zero unplanned downtime"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "storyteller"
    assert body["resolved_via"] == "first_attempt"


def test_dealmaker_stub_never_calls_claude(client, fake_claude):
    fake_claude([])  # empty queue -- a real call would raise AssertionError

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer qn-test-key"},
        json={
            "module": "dealmaker",
            "mode": "enterprise",
            "user_message": "Draft a proposal for the Chevron deal.",
            "context": {"deal_value": 150000},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "dealmaker"
    assert body["resolved_via"] == "graceful_fallback"
    assert body["generated_content"] == ""
    assert "not enabled" in body["strategic_critique"]


def test_modules_endpoint_reports_live_flags(client, fake_claude):
    fake_claude([])
    response = client.get("/v1/modules", headers={"Authorization": "Bearer qn-test-key"})
    assert response.status_code == 200
    by_id = {m["module_id"]: m for m in response.json()}
    assert by_id["visionary"]["live"] is True
    assert by_id["storyteller"]["live"] is True
    assert by_id["dealmaker"]["live"] is False
    assert by_id["negotiator"]["live"] is False
    assert by_id["locker_room"]["live"] is False
