import logging
from typing import List, Optional, Dict, Any, Tuple
from services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)


def get_basic_player_v2(player_id: int) -> Optional[Dict[str, Any]]:
    """Get basic player information.

    cswrating is set to the end_rating from the player's most recent
    tournament, falling back to the players.rating if none exists.
    """
    query = """
        SELECT
            p.id as playerid,
            p.name,
            p.country,
            COALESCE(
                (SELECT tr.end_rating FROM tournament_results tr
                 WHERE tr.player_id = p.id AND tr.end_rating IS NOT NULL
                 ORDER BY tr.date DESC LIMIT 1),
                p.rating
            ) as cswrating,
            p.photo as photourl
        FROM players p
        WHERE p.id = %s
    """
    return execute_query_one(query, (player_id,))


def get_player_stats_v2(player_id: int) -> Optional[Dict[str, Any]]:
    """Compute detailed career stats for a player.

    Returns a dict with all the fields needed for PlayerStatsV2, or
    None if the player has no results.
    """
    # --- Aggregate stats from player_results, and fetch opponent info ---
    # strategy: get all non-bye game results, join to find the opponent
    # result on the same game, then aggregate in Python.
    query = """
        SELECT
            pr.score,
            pr.result,
            g.id as game_id,
            g.round,
            opp_pr.score as opp_score,
            opp_pr.player_id as opp_player_id,
            opp_p.name as opp_name,
            opp_p.rating as opp_rating
        FROM player_results pr
        JOIN games g ON pr.game_id = g.id
        JOIN player_results opp_pr
            ON opp_pr.game_id = g.id
           AND opp_pr.player_id != pr.player_id
        JOIN players opp_p ON opp_pr.player_id = opp_p.id
        WHERE pr.player_id = %s
          AND pr.score > 0
        ORDER BY g.id
    """
    rows = execute_query(query, (player_id,))
    if not rows:
        return None

    # Trackers for aggregations
    total_games = 0
    wins = 0
    losses = 0
    draws = 0
    total_score = 0
    total_against = 0

    high_game = None
    high_game_opp = None
    low_game = None
    low_game_opp = None

    biggest_win_margin = None
    biggest_win_opp = None
    high_loss_score = None
    high_loss_opp = None
    low_win_score = None
    low_win_opp = None

    buckets = {
        'under300': 0,
        '300to399': 0,
        '400to499': 0,
        '500to599': 0,
        '600plus': 0,
    }

    for row in rows:
        score = row['score']
        opp_score = row['opp_score']
        result = row['result']
        opp_name = row['opp_name']

        # Skip byes (score == 0 already filtered above, but double-check)
        if score is None or score == 0:
            continue

        total_games += 1
        total_score += score
        total_against += opp_score

        if result == 1:
            wins += 1
        elif result == -1:
            losses += 1
        elif result == 0:
            draws += 1

        # High / low game
        if high_game is None or score > high_game:
            high_game = score
            high_game_opp = opp_name
        if low_game is None or score < low_game:
            low_game = score
            low_game_opp = opp_name

        # Biggest win margin
        if result == 1:
            margin = score - opp_score
            if biggest_win_margin is None or margin > biggest_win_margin:
                biggest_win_margin = margin
                biggest_win_opp = opp_name

            # Lowest winning score
            if low_win_score is None or score < low_win_score:
                low_win_score = score
                low_win_opp = opp_name

        # Highest losing score
        if result == -1:
            if high_loss_score is None or score > high_loss_score:
                high_loss_score = score
                high_loss_opp = opp_name

        # Scoring buckets
        if score < 300:
            buckets['under300'] += 1
        elif score < 400:
            buckets['300to399'] += 1
        elif score < 500:
            buckets['400to499'] += 1
        elif score < 600:
            buckets['500to599'] += 1
        else:
            buckets['600plus'] += 1

    win_pct = (wins / (wins + losses + draws) * 100) if (wins + losses + draws) > 0 else 0.0
    avg_score = total_score / total_games if total_games > 0 else 0.0
    avg_against = total_against / total_games if total_games > 0 else 0.0

    # Fetch bye count separately
    bye_count = _get_bye_count(player_id)

    return {
        'gamesPlayed': total_games,
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'byes': bye_count,
        'winPercentage': win_pct,
        'averageScore': avg_score,
        'averageAgainst': avg_against,
        'highGame': high_game,
        'highGameOpponent': high_game_opp,
        'lowGame': low_game,
        'lowGameOpponent': low_game_opp,
        'biggestWin': biggest_win_margin,
        'biggestWinOpponent': biggest_win_opp,
        'highLoss': high_loss_score,
        'highLossOpponent': high_loss_opp,
        'lowWin': low_win_score,
        'lowWinOpponent': low_win_opp,
        'gamesUnder300': buckets['under300'],
        'games300to399': buckets['300to399'],
        'games400to499': buckets['400to499'],
        'games500to599': buckets['500to599'],
        'games600plus': buckets['600plus'],
    }


def _get_bye_count(player_id: int) -> int:
    """Count byes (result=0, score=0 or NULL)."""
    query = """
        SELECT COUNT(*) as cnt
        FROM player_results
        WHERE player_id = %s
          AND result = 0
          AND (score IS NULL OR score = 0)
    """
    row = execute_query_one(query, (player_id,))
    return row['cnt'] if row else 0


def get_tournament_list_v2(player_id: int) -> List[Dict[str, Any]]:
    """Get tournament history for a player (v2 format)."""
    query = """
        SELECT
            tr.id as tourneyid,
            tr.tournament_name as name,
            tr.date,
            d.name as division,
            tr.wins,
            tr.losses,
            COALESCE(tr.byes, 0) as draws,
            COALESCE(tr.spread, 0) as spread,
            tr.position as place,
            tr.end_rating as end_rating,
            (COALESCE(tr.end_rating, 0) - COALESCE(tr.start_rating, 0)) as rating_change,
            tr.old_rating_dev as start_deviation,
            tr.new_rating_dev as end_deviation
        FROM tournament_results tr
        JOIN divisions d ON tr.division_id = d.id
        WHERE tr.player_id = %s
        ORDER BY tr.date DESC
    """
    return execute_query(query, (player_id,))


def get_tournament_rounds_v2(player_id: int, tourney_id: int) -> List[Dict[str, Any]]:
    """Get per-round results for a player at a specific tournament.

    Returns list of dicts with round, opponent_name, opponent_id,
    opponent_rating, result (W/L/D/B), score_for, score_against,
    player_rating_at_time, plus tournament-level fields.
    """
    # First get tournament-level info
    # tourney_id here is tournaments.id, not tournament_results.id
    t_info = execute_query_one(
        """
        SELECT
            tr.id as tr_id,
            tr.tournament_name,
            tr.date as tournament_date,
            tr.start_rating,
            d.name as division_name
        FROM tournament_results tr
        JOIN divisions d ON tr.division_id = d.id
        JOIN tournaments t ON d.tournament_id = t.id
        WHERE tr.player_id = %s AND t.id = %s
        """,
        (player_id, tourney_id),
    )
    if not t_info:
        return []

    tr_id = t_info['tr_id']
    player_start_rating = t_info['start_rating']

    query = """
        SELECT
            g.round,
            opp_p.name as opponent_name,
            opp_pr.player_id as opponent_id,
            opp_p.rating as opponent_rating,
            pr.score as score_for,
            opp_pr.score as score_against,
            CASE
                WHEN pr.result = 1 THEN 'W'
                WHEN pr.result = -1 THEN 'L'
                WHEN pr.result = 0 AND pr.score > 0 THEN 'D'
                WHEN pr.result = 0 AND (pr.score IS NULL OR pr.score = 0) THEN 'B'
                ELSE NULL
            END as result
        FROM player_results pr
        JOIN games g ON pr.game_id = g.id
        JOIN divisions d ON g.division_id = d.id
        JOIN tournaments t ON d.tournament_id = t.id
        JOIN player_results opp_pr
            ON opp_pr.game_id = g.id
           AND opp_pr.player_id != pr.player_id
        JOIN players opp_p ON opp_pr.player_id = opp_p.id
        WHERE pr.player_id = %s
          AND t.id = %s
        ORDER BY g.round ASC
    """
    rows = execute_query(query, (player_id, tourney_id))

    # Inject tournament-level fields into each row
    base = {
        'tournament_name': t_info['tournament_name'],
        'tournament_date': t_info['tournament_date'],
        'division_name': t_info['division_name'],
        'player_rating_at_time': player_start_rating,
    }
    for row in rows:
        row.update(base)

    return rows
