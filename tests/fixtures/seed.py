"""Deterministic test data for the WESPA API test suite.

The dataset is deliberately small but exercises the shapes the API cares about:
career aggregates, per-tournament averages, peak ratings, rankings filters,
byes, draws, head-to-head games, and missing data.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple


EVENT_ID = 501
TEST_OPEN = 1001
TEST_CHAMPIONSHIP = 1002
TEST_CLASSIC = 1003
OLD_TOURNAMENT = 1004
PROVISIONAL_CUP = 1005

DIVISION_IDS = {
    TEST_OPEN: 2001,
    TEST_CHAMPIONSHIP: 2002,
    TEST_CLASSIC: 2003,
    OLD_TOURNAMENT: 2004,
    PROVISIONAL_CUP: 2005,
}


def _result_for_round(round_no: int) -> int:
    """Deterministic pattern for player 1 in a pairing: 0 draw, 1 win, -1 loss."""
    remainder = round_no % 10
    if remainder == 0:
        return 0
    if remainder <= 6:
        return 1
    return -1


def _scores_for_round(round_no: int, p1: int, p2: int, result1: int) -> Tuple[int, int]:
    s1 = 300 + ((round_no * 17 + p1) % 401)
    s2 = 300 + ((round_no * 29 + p2) % 401)
    if result1 == 1:
        if s1 <= s2:
            s1 = s2 + 20
    elif result1 == -1:
        if s2 <= s1:
            s2 = s1 + 20
    else:
        s1 = s2 = 400 + round_no
    return s1, s2


class Seed:
    def __init__(self) -> None:
        self.today = date.today()
        self.players: Dict[int, Dict[str, Any]] = {}
        self.tournaments: Dict[int, Dict[str, Any]] = {}
        self.divisions: Dict[int, Dict[str, Any]] = {}
        self.stats: Dict[int, Dict[str, Any]] = {}
        self.tournament_stats: Dict[int, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        self._player_names = {101: "Alice Alpha", 102: "Bob Beta", 103: "Charlie Gamma",
                              104: "Dana Delta", 105: "Eve Epsilon", 106: "Frank Zeta",
                              107: "Grace Eta", 108: "Henry Theta", 109: "Ivy Iota",
                              110: "Jack Kappa", 111: "Kara Lambda", 112: "Liam Mu",
                              113: "Nora Nu"}

    def _init_stats(self, player_id: int) -> None:
        self.stats.setdefault(player_id, {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "byes": 0,
            "scores": [],
            "opp_scores": [],
            "opp_names": [],
            "spread": 0,
        })

    def _record_game(
        self,
        tournament_id: int,
        player_id: int,
        opponent_id: Optional[int],
        score: int,
        opponent_score: Optional[int],
        result: int,
        round_no: int,
    ) -> None:
        self._init_stats(player_id)
        stats = self.stats[player_id]
        tstats = self.tournament_stats[player_id].setdefault(tournament_id, {
            "rounds": [], "wins": 0, "losses": 0, "draws": 0, "spread": 0,
        })

        if opponent_id is None:
            # A bye is stored as result=0, score=0 with no opponent row.
            stats["byes"] += 1
            return

        stats["games"] += 1
        stats["scores"].append(score)
        stats["opp_scores"].append(opponent_score)
        stats["opp_names"].append(self._player_names[opponent_id])
        stats["spread"] += score - opponent_score

        if result == 1:
            stats["wins"] += 1
            tstats["wins"] += 1
        elif result == -1:
            stats["losses"] += 1
            tstats["losses"] += 1
        else:
            stats["draws"] += 1
            tstats["draws"] += 1

        tstats["rounds"].append({
            "round": round_no,
            "opponent_id": opponent_id,
            "score": score,
            "opponent_score": opponent_score,
            "result": result,
        })
        tstats["spread"] += score - opponent_score

    def _add_game(
        self,
        cur,
        tournament_id: int,
        round_no: int,
        p1: int,
        p2: Optional[int],
        score1: int,
        score2: Optional[int],
        result1: int,
    ) -> int:
        division_id = DIVISION_IDS[tournament_id]
        gcg_filename = f"{tournament_id}-{round_no}-{p1}.gcg"
        cur.execute(
            """INSERT INTO games (division_id, round, lexicon_id, gcg_filename)
               VALUES (%s, %s, 1, %s)""",
            (division_id, round_no, gcg_filename),
        )
        game_id = cur.lastrowid
        cur.execute(
            """INSERT INTO player_results (player_id, game_id, score, result)
               VALUES (%s, %s, %s, %s)""",
            (p1, game_id, score1, result1),
        )
        if p2 is not None:
            cur.execute(
                """INSERT INTO player_results (player_id, game_id, score, result)
                   VALUES (%s, %s, %s, %s)""",
                (p2, game_id, score2, -result1),
            )
        self._record_game(tournament_id, p1, p2, score1, score2, result1, round_no)
        if p2 is not None:
            self._record_game(tournament_id, p2, p1, score2, score1, -result1, round_no)
        return game_id

    def build(self) -> Dict[str, Any]:
        return {
            "today": self.today,
            "players": self.players,
            "player_names": dict(self._player_names),
            "tournaments": self.tournaments,
            "divisions": self.divisions,
            "stats": self.stats,
            "tournament_stats": dict(self.tournament_stats),
        }


def _insert_player(cur, player_id: int, name: str, country: str, rating: int,
                   total_games: int, last_played: Optional[date], *,
                   title: Optional[str] = None, norms: Optional[str] = None,
                   photo: Optional[str] = None) -> None:
    cur.execute(
        """INSERT INTO players
           (id, name, country, photo, suspended, deceased, current, provisional,
            total_games, last_played, rating, title, norms)
           VALUES (%s, %s, %s, %s, 0, 0, %s, %s, %s, %s, %s, %s, %s)""",
        (player_id, name, country, photo, 1 if total_games > 0 else 0,
         1 if total_games < 50 else 0, total_games, last_played, rating, title, norms),
    )


def seed_database(conn) -> Dict[str, Any]:
    seed = Seed()
    s = seed
    today = s.today
    recent = today - timedelta(days=30)
    old = today - timedelta(days=800)

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO events (id, start_date, end_date, link, sponsor, country, location)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (EVENT_ID, today - timedelta(days=500), today, "https://example.test/event",
             "Test Sponsor", "USA", "Testville"),
        )
        cur.execute("INSERT INTO lexicons (id, name) VALUES (1, 'CSW21')")

        _insert_player(cur, 101, "Alice Alpha", "USA", 1820, 60, recent,
                       title="M", norms="**", photo="https://example.test/alice.jpg")
        _insert_player(cur, 102, "Bob Beta", "GBR", 1720, 60, recent)
        _insert_player(cur, 103, "Charlie Gamma", "CAN", 1600, 4, recent)
        _insert_player(cur, 104, "Dana Delta", "USA", 1500, 0, None)
        _insert_player(cur, 105, "Eve Epsilon", "NZL", 1420, 60, old)
        _insert_player(cur, 106, "Frank Zeta", "USA", 1320, 60, recent)
        _insert_player(cur, 107, "Grace Eta", "USA", 1220, 60, recent)
        _insert_player(cur, 113, "Nora Nu", "USA", 500, 4, recent)

        cur.execute(
            "INSERT INTO player_alt_names (alt_name, player_id) VALUES (%s, %s)",
            ("BOBBY", 102),
        )

        tournament_defs = [
            (TEST_OPEN, "Test Open", today - timedelta(days=400), "A"),
            (TEST_CHAMPIONSHIP, "Test Championship", today - timedelta(days=200), "Open"),
            (TEST_CLASSIC, "Test Classic", today - timedelta(days=30), "Championship"),
            (OLD_TOURNAMENT, "Old Tournament", old, "A"),
            (PROVISIONAL_CUP, "Provisional Cup", today - timedelta(days=10), "Youth"),
        ]
        for tournament_id, name, tournament_date, division_name in tournament_defs:
            cur.execute(
                """INSERT INTO tournaments
                   (id, event_id, td, start_date, end_date, name, country, filename)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (tournament_id, EVENT_ID, "Test TD", tournament_date, tournament_date,
                 name, "USA", f"{tournament_id}.tou"),
            )
            cur.execute(
                """INSERT INTO divisions (id, tournament_id, name, length, number)
                   VALUES (%s, %s, %s, %s, %s)""",
                (DIVISION_IDS[tournament_id], tournament_id, division_name, 20, 1),
            )
            s.tournaments[tournament_id] = {
                "id": tournament_id,
                "name": name,
                "date": tournament_date,
                "division_id": DIVISION_IDS[tournament_id],
                "division_name": division_name,
            }
            s.divisions[DIVISION_IDS[tournament_id]] = {
                "id": DIVISION_IDS[tournament_id],
                "tournament_id": tournament_id,
                "name": division_name,
            }

        # Three twenty-game tournaments for the four ranked players.
        ranked_players = [101, 102, 106, 107]
        ratings_by_tournament = {
            TEST_OPEN: {101: (1750, 1780), 102: (1650, 1680),
                        106: (1250, 1280), 107: (1150, 1180)},
            TEST_CHAMPIONSHIP: {101: (1780, 1800), 102: (1680, 1700),
                                106: (1280, 1300), 107: (1180, 1200)},
            TEST_CLASSIC: {101: (1800, 1820), 102: (1700, 1720),
                           106: (1300, 1320), 107: (1200, 1220)},
        }

        for tournament_id in (TEST_OPEN, TEST_CHAMPIONSHIP, TEST_CLASSIC):
            for round_no in range(1, 21):
                if round_no % 2 == 0:
                    pairs = [(101, 102), (106, 107)]
                else:
                    pairs = [(101, 106), (102, 107)]
                for p1, p2 in pairs:
                    result1 = _result_for_round(round_no)
                    score1, score2 = _scores_for_round(round_no, p1, p2, result1)
                    s._add_game(cur, tournament_id, round_no, p1, p2,
                                score1, score2, result1)

        # One bye for player 101 in the first tournament.
        s._add_game(cur, TEST_OPEN, 21, 101, None, 0, None, 0)

        # A four-game provisional tournament for players 103 and 113.
        for round_no in range(1, 5):
            result1 = 1 if round_no <= 2 else -1
            score1, score2 = _scores_for_round(round_no, 103, 113, result1)
            s._add_game(cur, PROVISIONAL_CUP, round_no, 103, 113,
                        score1, score2, result1)

        # Tournament-level result rows.
        for tournament_id in (TEST_OPEN, TEST_CHAMPIONSHIP, TEST_CLASSIC):
            tournament = s.tournaments[tournament_id]
            for position, player_id in enumerate(ranked_players, start=1):
                tstats = s.tournament_stats[player_id][tournament_id]
                start_rating, end_rating = ratings_by_tournament[tournament_id][player_id]
                cur.execute(
                    """INSERT INTO tournament_results
                       (division_id, player_id, player_name, position, wins, losses,
                        byes, spread, prize_money, prize_currency, prize_ech_rate,
                        start_rating, end_rating, date, tournament_name, expected_wins,
                        old_world_rank, new_world_rank, old_national_rank,
                        new_national_rank, old_rating_dev, new_rating_dev)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (tournament["division_id"], player_id,
                     s._player_names[player_id], position,
                     tstats["wins"], tstats["losses"], tstats["draws"],
                     tstats["spread"], 0, "USD", "1",
                     start_rating, end_rating, tournament["date"],
                     tournament["name"], 10.0, 10, 10, 10, 10, 50, 40),
                )

        for player_id, start_rating, end_rating in ((103, 1600, 1600), (113, 500, 500)):
            tstats = s.tournament_stats[player_id][PROVISIONAL_CUP]
            tournament = s.tournaments[PROVISIONAL_CUP]
            cur.execute(
                """INSERT INTO tournament_results
                   (division_id, player_id, player_name, position, wins, losses,
                    byes, spread, start_rating, end_rating, date, tournament_name,
                    expected_wins, old_rating_dev, new_rating_dev)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tournament["division_id"], player_id, s._player_names[player_id],
                 1 if player_id == 103 else 2, tstats["wins"], tstats["losses"],
                 tstats["draws"], tstats["spread"], start_rating, end_rating,
                 tournament["date"], tournament["name"], 2.0, 80, 80),
            )

        # The old tournament exists for date filtering/search tests.
        # The old tournament deliberately has an end_rating different from
        # players.rating. The API contract is that players.rating is canonical,
        # so this exercises the fallback/source-of-truth behaviour.
        cur.execute(
            """INSERT INTO tournament_results
               (division_id, player_id, player_name, position, wins, losses, byes,
                spread, start_rating, end_rating, date, tournament_name,
                expected_wins, old_rating_dev, new_rating_dev)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (DIVISION_IDS[OLD_TOURNAMENT], 105, s._player_names[105], 1,
             0, 0, 0, 0, 1300, 1300, old, "Old Tournament", 0.0, 50, 50),
        )

    return seed.build()

