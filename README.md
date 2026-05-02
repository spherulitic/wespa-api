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

New endpoints with detailed player statistics and per-round tournament breakdowns.

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
- Result values: `W` (win), `L` (loss), `D` (draw), `B` (bye).

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
│   └── player_v2.py         # v2 player endpoints (/v2/player/...)
├── services/
│   ├── __init__.py
│   ├── db.py                # Database connection pool and helpers
│   ├── player_queries.py    # v1 player data queries
│   ├── headtohead_queries.py
│   └── player_v2_queries.py # v2 player stats and round queries
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
