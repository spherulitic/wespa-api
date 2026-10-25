def test_index_and_health(client):
    index = client.get("/")
    assert index.status_code == 200
    assert index.get_json()["status"] == "healthy"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.get_json() == {"status": "healthy", "service": "wespa-api"}


def test_v1_player_basic(client, world):
    response = client.get("/player.php?player=101")
    assert response.status_code == 200
    body = response.get_json()

    stats = world["stats"][101]
    assert body["playerid"] == 101
    assert body["name"] == "Alice Alpha"
    assert body["cswrating"] == 1820
    assert body["cswranking"] == 1
    assert body["w"] == stats["wins"]
    assert body["l"] == stats["losses"]
    assert body["t"] == stats["draws"]
    assert body["b"] == stats["byes"]
    assert body["country"] == "USA"
    assert body["photourl"] == "https://example.test/alice.jpg"
    assert body["twlrating"] is None
    assert body["twlranking"] is None


def test_v1_player_with_results(client, world):
    response = client.get("/player.php?player=101&results=1")
    assert response.status_code == 200
    body = response.get_json()

    assert body["tournamentCount"] == 3
    assert len(body["results"]) == 3

    latest = body["results"][0]
    assert latest["name"] == "Test Classic"
    assert latest["division"] == "Championship"
    assert latest["place"] == 1
    assert latest["totalplayers"] == 4
    assert latest["rating"] == 1800
    assert latest["ratingchange"] == 20
    assert latest["points"] == world["tournament_stats"][101][1003]["spread"]

    expected_average = (
        sum(game["score"] for game in world["tournament_stats"][101][1003]["rounds"])
        / len(world["tournament_stats"][101][1003]["rounds"])
    )
    assert round(float(latest["averagepoints"]), 2) == round(expected_average, 2)


def test_v1_player_missing_data_is_empty(client):
    assert client.get("/player.php?player=999999").get_json() == {}
    assert client.get("/player.php").get_json() == {}


def test_players_batch(client, world):
    response = client.get("/players.php?p=101+102")
    assert response.status_code == 200
    players = {player["playerid"]: player for player in response.get_json()["players"]}

    assert set(players) == {101, 102}
    assert players[101]["cswrating"] == 1820
    assert players[102]["cswrating"] == 1720
    assert players[101]["w"] == world["stats"][101]["wins"]
    assert players[102]["l"] == world["stats"][102]["losses"]


def test_players_batch_idsonly_placeholder(client):
    response = client.get("/players.php?p=101+102&idsonly=1")
    assert response.status_code == 200
    assert response.get_json()["players"] == [
        {"playerid": 101, "name": "Player 101"},
        {"playerid": 102, "name": "Player 102"},
    ]


def test_players_search(client):
    response = client.get("/players.php?search=Alice")
    assert response.status_code == 200
    players = response.get_json()["players"]
    assert [player["playerid"] for player in players] == [101]

    response = client.get("/players.php?search=bobby")
    assert response.status_code == 200
    players = response.get_json()["players"]
    assert [player["playerid"] for player in players] == [102]


def test_players_search_idsonly(client):
    response = client.get("/players.php?search=Alice&idsonly=1")
    assert response.status_code == 200
    assert response.get_json()["players"] == [{
        "playerid": 101,
        "name": "Alice Alpha",
        "country": "USA",
        "cswrating": 1820,
    }]


def test_players_all_idsonly_excludes_zero_game_players(client):
    response = client.get("/players.php?idsonly=1")
    assert response.status_code == 200
    ids = [player["playerid"] for player in response.get_json()["players"]]

    assert 101 in ids
    assert 104 not in ids  # no games
    assert ids == sorted(ids)


def test_players_idsonly_pagination(client):
    response = client.get("/players.php?idsonly=1&limit=3&offset=1")
    assert response.status_code == 200
    ids = [player["playerid"] for player in response.get_json()["players"]]
    assert ids == [102, 103, 105]


def test_players_without_arguments_returns_empty_list(client):
    response = client.get("/players.php")
    assert response.status_code == 200
    assert response.get_json() == []


def test_head_to_head(client):
    response = client.get("/headtohead.php?players=101+102")
    assert response.status_code == 200
    games = response.get_json()

    # Each game is returned in both orientations by the current query.
    assert len(games) == 60
    assert len({game["gameid"] for game in games}) == 30
    assert {game["player1"]["playerid"] for game in games} == {101, 102}
    assert {game["player2"]["playerid"] for game in games} == {101, 102}
    assert all(game["tourneyname"] for game in games)
    assert all(game["date"] for game in games)
    assert all(game["annotated"].endswith(".gcg") for game in games)


def test_head_to_head_requires_two_players(client):
    assert client.get("/headtohead.php").get_json() == []
    assert client.get("/headtohead.php?players=101").get_json() == []


def test_v1_player_query_count(client, query_count):
    response = client.get("/player.php?player=101&results=1")
    assert response.status_code == 200
    # profile, career totals, ranking, tournament history
    assert query_count["queries"] == 4
