def _headers():
    return {"Authorization": "test-api-key"}


def test_update_country_requires_auth(client):
    response = client.put("/v2/player/country", json=[])
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized: invalid API key"}

    response = client.put(
        "/v2/player/country",
        json=[],
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


def test_update_country_requires_valid_body(client):
    assert client.put(
        "/v2/player/country", data="not json", headers=_headers(),
        content_type="application/json",
    ).status_code == 400

    assert client.put(
        "/v2/player/country", json={"player_id": 101, "trigraph": "USA"},
        headers=_headers(),
    ).status_code == 400

    assert client.put(
        "/v2/player/country", json=[], headers=_headers(),
    ).status_code == 400


def test_update_country_updates_and_reports_validation_errors(client, db):
    response = client.put(
        "/v2/player/country",
        json=[
            {"player_id": 101, "trigraph": "can"},
            {"player_id": "not-an-int", "trigraph": "USA"},
            {"player_id": 102, "trigraph": "US"},
            {"player_id": 999999, "trigraph": "USA"},
            "not-an-object",
        ],
        headers=_headers(),
    )
    assert response.status_code == 207
    results = response.get_json()["results"]
    assert [result["status"] for result in results] == [
        "updated",
        "invalid_player_id",
        "invalid_trigraph",
        "player_not_found",
        "invalid_entry",
    ]
    assert results[0]["trigraph"] == "CAN"

    with db.cursor() as cur:
        cur.execute("SELECT country FROM players WHERE id = 101")
        assert cur.fetchone()[0] == "CAN"

    # Restore the fixture country so other tests see stable data.
    with db.cursor() as cur:
        cur.execute("UPDATE players SET country = 'USA' WHERE id = 101")


def test_update_country_all_success_returns_200(client, db):
    response = client.put(
        "/v2/player/country",
        json=[{"player_id": 102, "trigraph": "IRL"}],
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.get_json()["results"] == [{
        "index": 0,
        "player_id": 102,
        "trigraph": "IRL",
        "status": "updated",
    }]

    with db.cursor() as cur:
        cur.execute("UPDATE players SET country = 'GBR' WHERE id = 102")
