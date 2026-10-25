# WESPA API — Agent Guide

## Project
Flask 3.0 API for Scrabble tournament data. MySQL (PyMySQL). Two API versions: v1 (`.php` paths, cross-tables.com compat) and v2 (clean paths, richer data).

## Commands
```bash
python app.py              # dev server on :8080
docker build -t wespa-api . && docker run -p 8080:8080 --env-file .env wespa-api
pytest -q                  # API test suite (requires a MySQL test database, see below)
```
Tests live in `tests/` and run in GitHub Actions against MySQL 8.0 and 8.4.
`requirements-dev.txt` contains the test dependencies. The test suite creates and
seeds a dedicated `wespa_test` database; never point `TEST_DB_*` at production.

## Architecture
```
app.py                         → entrypoint, blueprint registration, cache/limiter init
config.py                      → DB, cache, rate-limit config from env
api/{name}.py                  → blueprints (routes)
services/{name}_queries.py     → SQL queries, no ORM
models/schemas.py              → DTOs with to_dict()
services/db.py                 → pymysql connection pool (execute_query / execute_query_one / execute_update)
```
`.env` is gitignored but required locally.

## API quirks
- **v1** returns empty `{}` or `[]` on missing data (not 404) — cross-tables compat.
- **v2** returns proper HTTP errors (404, 500, 401, 400, 207).
- `PUT /v2/player/country` requires `Authorization` header matching `UPDATE_API_KEY` env var.
- `tourney_id` everywhere = `tournaments.id` (not `tournament_results.id`).
- Rankings: only players with ≥50 games and activity in last 2 years.

## Data quirks
- `cswrating` = `players.rating`; the tournament loader maintains it from the latest tournament `end_rating`.
- Same-date tournaments: the loader's choice of the latest rating is currently ambiguous; the API deliberately trusts `players.rating`. Fixing the loader's tie-break is a separate follow-up.
- `opponent_rating` in rounds = opponent's `start_rating` for that tournament (not current overall rating).
- `result` values: `W` (win), `L` (loss), `D` (draw), `B` (bye).
- Bye: `result=0 AND (score IS NULL OR score = 0)`.
- `tournament_results.wins` / `.losses` are floats (half-point byes possible).
- `tournament_results.byes` stores *draws*, not byes.
- Peak ratings (`peakRatingLastTwoYears`, `peakRatingAllTime`) exclude provisional tournaments (<50 cumulative games).
- `wins`/`losses`/`draws`/`spread` output as floats in v2 tournament endpoints (not int).
