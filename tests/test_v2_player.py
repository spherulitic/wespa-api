import statistics

import pytest


def _career(world, player_id):
    return world["stats"][player_id]


def _tournament_average(world, player_id, tournament_id):
    rounds = world["tournament_stats"][player_id][tournament_id]["rounds"]
    return (
        round(statistics.mean(round_["score"] for round_ in rounds), 2),
        round(statistics.mean(round_["opponent_score"] for round_ in rounds), 2),
    )


def test_v2_player_profile_stats_and_peaks(client, world):
    response = client.get("/v2/player/101")
    assert response.status_code == 200
    body = response.get_json()

    stats = _career(world, 101)
    assert body["playerid"] == 101
    assert body["name"] == "Alice Alpha"
    assert body["country"] == "USA"
    assert body["title"] == "M"
    assert body["norms"] == "**"
    assert body["cswrating"] == 1820
    assert body["photourl"] == "https://example.test/alice.jpg"
    assert body["peakRatingLastTwoYears"] == 1820
    assert body["peakRatingAllTime"] == 1820

    player_stats = body["stats"]
    assert player_stats["gamesPlayed"] == stats["games"] == 60
    assert int(player_stats["wins"]) == stats["wins"]
    assert int(player_stats["losses"]) == stats["losses"]
    assert int(player_stats["draws"]) == stats["draws"]
    assert int(player_stats["byes"]) == stats["byes"] == 1
    assert float(player_stats["winPercentage"]) == 60.0
    assert float(player_stats["averageScore"]) == round(statistics.mean(stats["scores"]), 2)
    assert float(player_stats["averageAgainst"]) == round(statistics.mean(stats["opp_scores"]), 2)
    assert player_stats["highGame"] == max(stats["scores"])
    assert player_stats["lowGame"] == min(stats["scores"])
    assert player_stats["highGameOpponent"] in stats["opp_names"]
    assert player_stats["lowGameOpponent"] in stats["opp_names"]
    assert (
        int(player_stats["gamesUnder300"])
        + int(player_stats["games300to399"])
        + int(player_stats["games400to499"])
        + int(player_stats["games500to599"])
        + int(player_stats["games600plus"])
        == stats["games"]
    )


def test_v2_player_tournament_list(client, world):
    response = client.get("/v2/player/101")
    assert response.status_code == 200
    tournaments = response.get_json()["tournaments"]

    assert len(tournaments) == 3
    latest = tournaments[0]
    assert latest["tourneyid"] == 1003
    assert latest["name"] == "Test Classic"
    assert latest["date"] == world["tournaments"][1003]["date"].isoformat()
    assert latest["division"] == "Championship"
    assert latest["wins"] == float(world["tournament_stats"][101][1003]["wins"])
    assert latest["losses"] == float(world["tournament_stats"][101][1003]["losses"])
    assert latest["draws"] == world["tournament_stats"][101][1003]["draws"]
    assert latest["spread"] == world["tournament_stats"][101][1003]["spread"]
    assert latest["place"] == 1
    assert latest["endRating"] == 1820
    assert latest["ratingChange"] == 20

    average_score, average_against = _tournament_average(world, 101, 1003)
    assert latest["averageScore"] == average_score
    assert latest["averageAgainst"] == average_against


def test_v2_player_without_tournaments_uses_rating_fallback(client):
    response = client.get("/v2/player/104")
    assert response.status_code == 200
    body = response.get_json()

    assert body["cswrating"] == 1500
    assert body["peakRatingLastTwoYears"] is None
    assert body["peakRatingAllTime"] is None
    assert body["tournaments"] == []
    assert body["stats"]["gamesPlayed"] == 0


def test_v2_player_provisional_has_no_peak(client):
    response = client.get("/v2/player/103")
    assert response.status_code == 200
    body = response.get_json()

    assert body["cswrating"] == 1600
    assert body["peakRatingLastTwoYears"] is None
    assert body["peakRatingAllTime"] is None
    assert body["stats"]["gamesPlayed"] == 4


def test_v2_player_not_found(client):
    response = client.get("/v2/player/999999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Player not found"}


def test_v2_player_uses_players_rating_as_source_of_truth(client):
    response = client.get("/v2/player/105")
    assert response.status_code == 200
    body = response.get_json()

    # players.rating is canonical even when a tournament's end_rating differs.
    assert body["cswrating"] == 1420
    assert body["tournaments"][0]["endRating"] == 1300


def test_v2_player_tournament_rounds(client, world):
    response = client.get("/v2/player/101/tournaments/1003")
    assert response.status_code == 200
    body = response.get_json()

    assert body["playerid"] == 101
    assert body["tourneyid"] == 1003
    assert body["name"] == "Test Classic"
    assert body["date"] == world["tournaments"][1003]["date"].isoformat()
    assert body["division"] == "Championship"
    assert len(body["rounds"]) == 20

    first = body["rounds"][0]
    expected = world["tournament_stats"][101][1003]["rounds"][0]
    assert first["round"] == 1
    assert first["opponent_id"] == expected["opponent_id"]
    assert first["opponent_name"] == world["player_names"][expected["opponent_id"]]
    assert first["score_for"] == expected["score"]
    assert first["score_against"] == expected["opponent_score"]
    assert first["result"] == {1: "W", -1: "L", 0: "D"}[expected["result"]]
    assert first["player_rating_at_time"] == 1800


def test_v2_player_tournament_rounds_excludes_bye(client):
    response = client.get("/v2/player/101/tournaments/1001")
    assert response.status_code == 200
    assert len(response.get_json()["rounds"]) == 20


def test_v2_player_tournament_rounds_not_found(client):
    assert client.get("/v2/player/999999/tournaments/1003").status_code == 404
    assert client.get("/v2/player/101/tournaments/999999").status_code == 404


def test_v2_player_query_count_is_characterised(client, query_count):
    response = client.get("/v2/player/101")
    assert response.status_code == 200
    # profile + stats + opponents + byes + tournaments. Peak ratings are
    # computed from the tournament rows already fetched (no extra queries).
    assert query_count["queries"] == 5


def test_v2_player_response_is_cached(client, query_count):
    response = client.get("/v2/player/101")
    assert response.status_code == 200
    first_body = response.get_json()
    assert query_count["queries"] == 5

    queries_before_second_request = query_count["queries"]
    response = client.get("/v2/player/101")
    assert response.status_code == 200
    assert response.get_json() == first_body
    assert query_count["queries"] == queries_before_second_request


def test_v2_player_returns_503_when_database_is_unavailable(client, monkeypatch):
    import pymysql
    from services import db as db_module

    def unavailable():
        raise pymysql.err.OperationalError(2003, "database is down")

    monkeypatch.setattr(db_module.db_pool, "get_connection", unavailable)
    response = client.get("/v2/player/101")

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.get_json() == {"error": "Service temporarily unavailable"}
