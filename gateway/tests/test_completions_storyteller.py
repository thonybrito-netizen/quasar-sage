import json


def test_storyteller_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Draft appeals to fear of obsolescence, not just cost savings.",
            "generated_content": "Your machines were offline for 14 hours last month. What did that cost the floor?",
            "suggested_next_action": "advance_to_locker_room",
            "sourced_fields": {"14 hours": "downtime_hours"},
            "vanity_metric_audit": {"leans_on_vanity_metrics": False, "reasoning": "Cites downtime cost, an operational outcome, not a vanity metric."},
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


def test_dealmaker_enterprise_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Economic Buyer confirmed, deal is healthy.",
            "generated_content": "Zero-latency decisions let the Plant Manager hit Q3 quotas.",
            "suggested_next_action": None,
            "sourced_fields": {"VP Operations": "economic_buyer"},
            "vanity_metric_audit": {"leans_on_vanity_metrics": False, "reasoning": "Frames the feature as a quota-hitting outcome for a named stakeholder."},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer qn-test-key"},
        json={
            "module": "dealmaker",
            "mode": "enterprise",
            "user_message": "Draft a proposal for the Chevron deal.",
            "context": {"deal_value": 150000, "economic_buyer": "VP Operations"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "dealmaker"
    assert body["mode"] == "enterprise"
    assert body["resolved_via"] == "first_attempt"


def test_dealmaker_retail_mode_selects_retail_prompt(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Countdown is backed by real inventory data.",
            "generated_content": "Only 4 left in stock -- order today.",
            "suggested_next_action": None,
            "sourced_fields": {"4 left": "stock_remaining"},
            "vanity_metric_audit": {"leans_on_vanity_metrics": False, "reasoning": "Real inventory-backed urgency, not a vanity metric at all."},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer qn-test-key"},
        json={
            "module": "dealmaker",
            "mode": "retail",
            "user_message": "Write urgency copy for this product page.",
            "context": {"stock_remaining": 4},
        },
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "retail"


def test_negotiator_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Walk-Away Ledger is defined, safe to proceed.",
            "generated_content": "How would a number like that work on your end?",
            "suggested_next_action": None,
            "sourced_fields": {"50000": "walk_away_value"},
            "vanity_metric_audit": {"leans_on_vanity_metrics": False, "reasoning": "Negotiation coaching, no metrics of any kind cited."},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer lo-test-key"},
        json={
            "module": "negotiator",
            "user_message": "They're asking for a 15% discount, how do I respond?",
            "context": {"walk_away_value": 50000, "counterpart_position": "15% discount"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "negotiator"
    assert body["resolved_via"] == "first_attempt"


def test_locker_room_happy_path(client, fake_claude):
    good_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Kill Criteria defined: 20 new orders in 30 days. Window not elapsed, too early to call it.",
            "generated_content": "Campaign is launch-ready.",
            "suggested_next_action": None,
            "sourced_fields": {"20 new orders in 30 days": "kill_criteria_target"},
            "vanity_metric_audit": {"leans_on_vanity_metrics": False, "reasoning": "Judged strictly against the client's own order-count Kill Criteria."},
        }
    )
    fake_claude([good_response])

    response = client.post(
        "/v1/completions",
        headers={"Authorization": "Bearer qn-test-key"},
        json={
            "module": "locker_room",
            "user_message": "Is this campaign ready to launch?",
            "context": {"kill_criteria_target": "20 new orders in 30 days"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "locker_room"
    assert body["resolved_via"] == "first_attempt"


def test_modules_endpoint_reports_live_flags(client, fake_claude):
    fake_claude([])
    response = client.get("/v1/modules", headers={"Authorization": "Bearer qn-test-key"})
    assert response.status_code == 200
    by_id = {m["module_id"]: m for m in response.json()}
    assert by_id["visionary"]["live"] is True
    assert by_id["storyteller"]["live"] is True
    assert by_id["dealmaker"]["live"] is True
    assert by_id["negotiator"]["live"] is True
    assert by_id["locker_room"]["live"] is True
