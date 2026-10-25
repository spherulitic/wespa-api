def test_v2_tournament_details(client, world):
    response = client.get("/v2/tournament/1003")
    assert response.status_code == 200
    body = response.get_json()

    assert body["tourneyid"] == 1003
    assert body["name"] == "Test Classic"
    assert body["date"] == world["tournaments"][1003]["date"].isoformat()
    assert body["location"] == "Testville, USA"
    assert body["total_players"] == 4
    assert len(body["divisions"]) == 1

    division = body["divisions"][0]
    assert division["division"] == 1
    assert division["name"] == "Championship"
    assert len(division["standings"]) == 4
    assert division["standings"][0]["playerid"] == 101
    assert division["standings"][0]["place"] == 1
    assert division["standings"][0]["startRating"] == 1800
    assert division["standings"][0]["endRating"] == 1820


def test_v2_tournament_not_found(client):
    response = client.get("/v2/tournament/999999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Tournament not found"}


def test_v2_division_ratings(client):
    response = client.get("/v2/tournament/1003/division/1/ratings")
    assert response.status_code == 200
    ratings = response.get_json()["ratings"]

    assert len(ratings) == 4
    first = ratings[0]
    assert first["playerid"] == 101
    assert first["name"] == "Alice Alpha"
    assert first["expectedWins"] == 10.0
    assert first["actualWins"] == 12.0
    assert first["startRating"] == 1800
    assert first["endRating"] == 1820
    assert first["ratingChange"] == 20


def test_v2_division_ratings_not_found(client):
    assert client.get("/v2/tournament/999999/division/1/ratings").status_code == 404
    assert client.get("/v2/tournament/1003/division/99/ratings").status_code == 404


def test_v2_division_stats(client):
    response = client.get("/v2/tournament/1003/division/1/stats")
    assert response.status_code == 200
    body = response.get_json()

    for category in ("highWin", "highLoss", "highSpread", "highCombined", "upsets"):
        assert category in body
        assert isinstance(body[category], list)

    assert body["highWin"]
    assert body["highCombined"]
    assert body["highWin"][0]["rank"] == 1
    assert body["highCombined"][0]["rank"] == 1
    assert body["highWin"][0]["player_id"] in {101, 102, 106, 107}


def test_v2_division_stats_not_found(client):
    assert client.get("/v2/tournament/999999/division/1/stats").status_code == 404
    assert client.get("/v2/tournament/1003/division/99/stats").status_code == 404


def test_tournament_search(client):
    response = client.get("/tournaments/search?q=Classic")
    assert response.status_code == 200
    tournaments = response.get_json()["tournaments"]
    assert [tournament["tourneyid"] for tournament in tournaments] == [1003]

    response = client.get("/tournaments/search?country=USA")
    assert response.status_code == 200
    assert len(response.get_json()["tournaments"]) == 5

    response = client.get("/tournaments/search?from=2020-01-01&to=2099-01-01")
    assert response.status_code == 200
    assert {t["tourneyid"] for t in response.get_json()["tournaments"]} == {
        1001, 1002, 1003, 1004, 1005,
    }


def test_tournament_search_requires_a_filter(client):
    response = client.get("/tournaments/search")
    assert response.status_code == 400
    assert response.get_json()["tournaments"] == []
    assert "error" in response.get_json()


def test_rankings_pagination(client):
    response = client.get("/v2/rankings?page=1&per_page=2")
    assert response.status_code == 200
    body = response.get_json()

    assert body["page"] == 1
    assert body["per_page"] == 2
    assert body["total"] == 4
    assert body["total_pages"] == 2
    assert [player["rating"] for player in body["players"]] == [1820, 1720]
    assert [player["rank"] for player in body["players"]] == [1, 2]

    response = client.get("/v2/rankings?page=2&per_page=2")
    body = response.get_json()
    assert [player["rating"] for player in body["players"]] == [1320, 1220]
    assert [player["rank"] for player in body["players"]] == [3, 4]


def test_rankings_excludes_inactive_and_provisional_players(client):
    response = client.get("/v2/rankings?per_page=100")
    ids = [player["playerid"] for player in response.get_json()["players"]]
    assert 103 not in ids  # provisional
    assert 104 not in ids  # no games
    assert 105 not in ids  # inactive for > 2 years


def test_rankings_search_jumps_to_player_page(client):
    response = client.get("/v2/rankings?search=Alice&per_page=2")
    assert response.status_code == 200
    body = response.get_json()
    assert body["page"] == 1
    assert body["players"][0]["playerid"] == 101

    response = client.get("/v2/rankings?search=Grace&per_page=2")
    assert response.status_code == 200
    body = response.get_json()
    assert body["page"] == 2
    assert body["players"][-1]["playerid"] == 107

    response = client.get("/v2/rankings?search=Bob&per_page=2")
    assert response.status_code == 200
    assert response.get_json()["page"] == 1


def test_rankings_parameter_clamping(client):
    response = client.get("/v2/rankings?page=0&per_page=1000")
    assert response.status_code == 200
    body = response.get_json()
    assert body["page"] == 1
    assert body["per_page"] == 100
    assert body["total_pages"] == 1


def test_rankings_tournament_count(client):
    response = client.get("/v2/rankings/tournament-count")
    assert response.status_code == 200
    assert response.get_json() == {"total_tournaments": 5}


def test_rankings_query_count(client, query_count):
    response = client.get("/v2/rankings?page=1&per_page=3")
    assert response.status_code == 200
    # One count query and one page query.
    assert query_count["queries"] == 2


def test_rankings_response_is_cached(client, query_count):
    response = client.get("/v2/rankings?page=1&per_page=2")
    assert response.status_code == 200
    first_body = response.get_json()
    assert query_count["queries"] == 2

    queries_before_second_request = query_count["queries"]
    response = client.get("/v2/rankings?page=1&per_page=2")
    assert response.status_code == 200
    assert response.get_json() == first_body
    assert query_count["queries"] == queries_before_second_request
