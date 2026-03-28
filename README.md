# WESPA Scrabble API

Flask-based API for Scrabble tournament data, compatible with cross-tables.com API format.

## Endpoints

- `GET /player.php?player={id}` - Get basic player info
- `GET /player.php?player={id}&results=1` - Get player info with tournament history
- `GET /players.php?playerlist={id1},{id2},...` - Get multiple players (max 50)
- `GET /players.php?search={name}` - Search players by name
- `GET /players.php?idsonly=1` - Get all player IDs and names (limit 200)
- `GET /players.php?search={name}&idsonly=1` - Search players (IDs only)
- `GET /headtohead.php?players={id1}+{id2}+...` - Get head-to-head games

## Deployment

### Environment Variables
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 3306)
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name
- `RATELIMIT_DEFAULT` - Rate limit (default: "100 per minute")

### Docker Build
```bash
docker build -t wespa-api .
docker run -p 8080:8080 --env-file .env wespa-api
