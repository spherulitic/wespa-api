# WESPA Scrabble API

Flask-based API for Scrabble tournament data, compatible with cross-tables.com API format.

## Endpoints

### v1 (Legacy — maintained for existing clients)

All v1 endpoints use `.php` extension paths for cross-tables compatibility.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/player.php?player={id}` | Get basic player info |
| GET | `/player.php?player={id}&results=1` | Player info with tournament history |
| GET | `/players.php?p={id1}+{id2}+...` | Get multiple players by ID (max 50) |
| GET | `/players.php?search={name}` | Search players by name |
| GET | `/players.php?idsonly=1` | Get all player IDs and names |
| GET | `/players.php?search={name}&idsonly=1` | Search players (IDs only) |
| GET | `/headtohead.php?players={id1}+{id2}+...` | Head-to-head games between players |
| GET | `/health` | Health check |

### v2 (Clean paths with enhanced data)

New endpoints with detailed player statistics, per-round tournament breakdowns, and rankings.

#### Player Profile

```
GET /v2/player/{player_id}
```

Returns a player's profile, detailed career statistics, and tournament history.

**Response shape:**

```json
{
  "playerid": 3039,
  "name": "Zachary Dang",
  "country": "USA",
  "cswrating": 1764,
  "norms": "**"
  "photourl": "https://legacy.wespa.org/aardvark/icons/zacharydang.jpg",
  "stats": {
    "gamesPlayed": 68,
    "wins": 33,
    "losses": 34,
    "draws": 1,
    "byes": 0,
    "winPercentage": 48.53,
    "averageScore": 423.22,
    "averageAgainst": 414.90,
    "highGame": 588,
    "highGameOpponent": "Ian Coventry",
    "lowGame": 291,
    "lowGameOpponent": "Winter",
    "biggestWin": 287,
    "biggestWinOpponent": "Gary Oliver",
    "highLoss": 458,
    "highLossOpponent": "Victoria Kingham",
    "lowWin": 373,
    "lowWinOpponent": "Winter",
    "gamesUnder300": 2,
    "games300to399": 23,
    "games400to499": 33,
    "games500to599": 10,
    "games600plus": 0
  },
  "title": "M"
  "tournaments": [
    {
      "tourneyid": 52540,
      "name": "UK Open - Final Fling",
      "date": "2026-01-10",
      "division": "A",
      "wins": 6,
      "losses": 9,
      "draws": 0,
      "spread": -274,
      "place": 15,
      "endRating": 1691,
      "ratingChange": -73,
      "startDeviation": 67,
      "endDeviation": 42
    }
  ]
}
```

#### Tournament Round Details

```
GET /v2/player/{player_id}/tournaments/{tourney_id}
```

Returns per-round results for a player at a specific tournament.

**Response shape:**

```json
{
  "playerid": 3039,
  "tourneyid": 52540,
  "name": "UK Open - Final Fling",
  "date": "2026-01-10",
  "division": "A",
  "rounds": [
    {
      "round": 1,
      "opponent_name": "Nuala O'Rourke",
      "opponent_id": 61,
      "opponent_rating": 1704,
      "result": "L",
      "score_for": 360,
      "score_against": 388,
      "player_rating_at_time": 1764
    }
  ]
}
```

- `cswrating` is the player's `end_rating` from their most recent tournament, or falls back to the `players.rating` column if no tournaments exist.
- `endRating` / `ratingChange` / `startDeviation` / `endDeviation` in each tournament entry reflect the rating and rating deviation at the end of that tournament.
- `opponent_rating` in each round is the opponent's **start rating** for the tournament (from `tournament_results.start_rating`), not their current overall rating.
- Result values: `W` (win), `L` (loss), `D` (draw), `B` (bye).

#### Rankings

```
GET /v2/rankings?page=1&per_page=50&search=
```

Returns a paginated list of active players sorted by rating descending.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-based) |
| `per_page` | int | 50 | Players per page (max 100) |
| `search` | string | (optional) | Player name to jump to their page |

**Response shape:**

```json
{
  "page": 1,
  "per_page": 50,
  "total": 987,
  "total_pages": 20,
  "players": [
    {
      "rank": 1,
      "playerid": 3039,
      "name": "Zachary Dang",
      "country": "USA",
      "rating": 1764,
      "total_games": 1200,
      "last_played": "2026-05-10"
    }
  ]
}
```

- Rankings are computed using each player's latest `tournament_results.end_rating`, falling back to `players.rating` if no tournament exists.
- Only players with at least 50 games and activity in the last 2 years are included.

#### Latest Tournament

```
GET /v2/rankings/latest-tournament
```

Returns the name and end date of the most recent tournament.

**Response shape:**

```json
{
  "name": "Causeway Challenge",
  "date": "2026-05-25"
}
```

#### Tournament Details

```
GET /v2/tournament/{tourney_id}
```

Returns tournament-level info along with all divisions and their full standings.

**Response shape:**

```json
{
  "tourneyid": 52540,
  "name": "UK Open - Final Fling",
  "date": "2026-01-10",
  "location": "Birmingham, England",
  "total_players": 45,
  "divisions": [
    {
      "division": 1,
      "name": "Division A",
      "standings": [
        {
          "place": 1,
          "playerid": 3039,
          "name": "Zachary Dang",
          "wins": 12,
          "losses": 3,
          "draws": 0,
          "spread": 1054,
          "points": 24
        }
      ]
    }
  ]
}
```

#### Division Ratings

```
GET /v2/tournament/{tourney_id}/division/{division_index}/ratings
```

Returns rating and rank information for all players in a specific division of a tournament.

**Response shape:**

```json
{
  "ratings": [
    {
      "playerid": 3039,
      "name": "Zachary Dang",
      "startRating": 1764,
      "endRating": 1791,
      "ratingChange": 27,
      "expWins": 8.5,
      "actWins": 12,
      "oldWorldRank": 1,
      "newWorldRank": 1,
      "oldNationRank": 1,
      "newNationRank": 1,
      "startDeviation": 67,
      "endDeviation": 42
    }
  ]
}
```

- `actWins` is the raw win count from the standings (byes are not counted as wins).

#### Division Stats

```
GET /v2/tournament/{tourney_id}/division/{division_index}/stats
```

Returns detailed match statistics for a division, including highest wins, losses, spreads, combined scores, and upsets.

**Response shape:**

```json
{
  "highWin": [
    {
      "round": 5,
      "player": "Zachary Dang",
      "opponent": "Ian Coventry",
      "score_for": 588,
      "score_against": 301,
      "spread": 287
    }
  ],
  "highLoss": [],
  "highSpread": [],
  "highCombined": [],
  "upsets": []
}
```

### Tournament Search

```
GET /tournaments/search?q={name}&country={code}&from={date}&to={date}
```

Search tournaments by name, country, and/or date range. All parameters are optional, but at least one must be provided.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Partial tournament name (case-insensitive) |
| `country` | string | 3-letter country code (e.g. GBR, USA) |
| `from` | string | Start date (YYYY-MM-DD) |
| `to` | string | End date (YYYY-MM-DD) |

**Response shape:**

```json
{
  "tournaments": [
    {
      "tourneyid": 52540,
      "name": "UK Open - Final Fling",
      "start_date": "2026-01-10",
      "end_date": "2026-01-12",
      "country": "GBR",
      "location": "Birmingham"
    }
  ]
}
```

## Project Structure

```
wespa-api/
├── app.py                   # Flask application entry point
├── config.py                # Configuration (DB, cache, rate limiting)
├── api/
│   ├── __init__.py
│   ├── player.py            # v1 player endpoint (/player.php)
│   ├── players.py           # v1 players endpoint (/players.php)
│   ├── headtohead.py        # v1 head-to-head endpoint (/headtohead.php)
│   ├── player_v2.py         # v2 player endpoints (/v2/player/...)
│   ├── rankings_v2.py       # v2 rankings endpoints (/v2/rankings)
│   ├── division_v2.py       # v2 division endpoint
│   ├── tournament_v2.py     # v2 tournament endpoint
│   └── tournament_search.py # Tournament search endpoint
├── services/
│   ├── __init__.py
│   ├── db.py                # Database connection pool and helpers
│   ├── player_queries.py    # v1 player data queries
│   ├── headtohead_queries.py
│   ├── player_v2_queries.py # v2 player stats and round queries
│   ├── rankings_queries.py  # v2 rankings queries
│   ├── division_v2_queries.py # v2 division queries
│   ├── tournament_v2_queries.py # v2 tournament queries
│   └── tournament_search_queries.py # Tournament search queries
├── models/
│   ├── __init__.py
│   └── schemas.py           # Data transfer objects (v1 and v2)
└── requirements.txt
```

## Deployment

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `DB_USER` | Database user | `root` |
| `DB_PASSWORD` | Database password | (empty) |
| `DB_NAME` | Database name | `wespa` |
| `RATELIMIT_DEFAULT` | API rate limit | `100 per minute` |

### Docker Build

```bash
docker build -t wespa-api .
docker run -p 8080:8080 --env-file .env wespa-api
```
