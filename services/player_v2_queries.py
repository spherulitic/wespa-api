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
            p.title,
            p.norms,
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

    All aggregation happens in a single SQL query, plus one extra query
    for the five opponent names (instead of five separate lookups).
    """
    # --- Single aggregation query ---
    query = """
        SELECT
            COUNT(*) as total_games,
            SUM(CASE WHEN pr.result = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN pr.result = -1 THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN pr.result = 0 AND pr.score > 0 THEN 1 ELSE 0 END) as draws,
            ROUND(AVG(pr.score), 2) as average_score,
            ROUND(AVG(opp_pr.score), 2) as average_against,
            MAX(pr.score) as high_game,
            MIN(pr.score) as low_game,
            MAX(CASE WHEN pr.result = 1 THEN pr.score - opp_pr.score ELSE 0 END) as biggest_win_margin,
            MAX(CASE WHEN pr.result = -1 THEN pr.score ELSE 0 END) as high_loss_score,
            MIN(CASE WHEN pr.result = 1 THEN pr.score ELSE NULL END) as low_win_score,
            SUM(CASE WHEN pr.score < 300 THEN 1 ELSE 0 END) as under300,
            SUM(CASE WHEN pr.score >= 300 AND pr.score < 400 THEN 1 ELSE 0 END) as score300to399,
            SUM(CASE WHEN pr.score >= 400 AND pr.score < 500 THEN 1 ELSE 0 END) as score400to499,
            SUM(CASE WHEN pr.score >= 500 AND pr.score < 600 THEN 1 ELSE 0 END) as score500to599,
            SUM(CASE WHEN pr.score >= 600 THEN 1 ELSE 0 END) as score600plus
        FROM player_results pr
        JOIN games g ON pr.game_id = g.id
        JOIN player_results opp_pr
            ON opp_pr.game_id = g.id
           AND opp_pr.player_id != pr.player_id
        WHERE pr.player_id = %s
          AND pr.score > 0
    """
    row = execute_query_one(query, (player_id,))
    if not row or not row['total_games']:
        return None

    # --- Single query for all five opponent names ---
    # Uses GROUP_CONCAT with ordering to pick the first match per category.
    opp_query = """
        SELECT
            SUBSTRING_INDEX(GROUP_CONCAT(opp_p.name ORDER BY pr.score DESC), ',', 1) as high_game_opp,
            SUBSTRING_INDEX(GROUP_CONCAT(opp_p.name ORDER BY pr.score ASC), ',', 1) as low_game_opp,
            SUBSTRING_INDEX(GROUP_CONCAT(opp_p.name ORDER BY (pr.score - opp_pr.score) DESC), ',', 1) as biggest_win_opp,
            SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN pr.result = -1 THEN opp_p.name END ORDER BY pr.score DESC), ',', 1) as high_loss_opp,
            SUBSTRING_INDEX(GROUP_CONCAT(CASE WHEN pr.result = 1 THEN opp_p.name END ORDER BY pr.score ASC), ',', 1) as low_win_opp
        FROM player_results pr
        JOIN games g ON pr.game_id = g.id
        JOIN player_results opp_pr ON opp_pr.game_id = g.id AND opp_pr.player_id != pr.player_id
        JOIN players opp_p ON opp_pr.player_id = opp_p.id
        WHERE pr.player_id = %s AND pr.score > 0
    """
    opp_row = execute_query_one(opp_query, (player_id,))

    bye_count = _get_bye_count(player_id)

    total_games = row['total_games']
    wins = row['wins']
    losses = row['losses']
    draws = row['draws']
    win_pct = (wins / (wins + losses + draws) * 100) if (wins + losses + draws) > 0 else 0.0

    return {
        'gamesPlayed': total_games,
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'byes': bye_count,
        'winPercentage': round(win_pct, 2),
        'averageScore': row['average_score'],
        'averageAgainst': row['average_against'],
        'highGame': row['high_game'],
        'highGameOpponent': opp_row['high_game_opp'] if opp_row else None,
        'lowGame': row['low_game'],
        'lowGameOpponent': opp_row['low_game_opp'] if opp_row else None,
        'biggestWin': row['biggest_win_margin'],
        'biggestWinOpponent': opp_row['biggest_win_opp'] if opp_row else None,
        'highLoss': row['high_loss_score'],
        'highLossOpponent': opp_row['high_loss_opp'] if opp_row else None,
        'lowWin': row['low_win_score'],
        'lowWinOpponent': opp_row['low_win_opp'] if opp_row else None,
        'gamesUnder300': row['under300'],
        'games300to399': row['score300to399'],
        'games400to499': row['score400to499'],
        'games500to599': row['score500to599'],
        'games600plus': row['score600plus'],
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
    """Get tournament history for a player (v2 format), including per-tournament
    average score/against, all in a single query.

    Uses a CTE to compute per-tournament averages and joins them to the
    main tournament list, avoiding a separate round-trip.
    """
    query = """
        WITH tourney_avgs AS (
            SELECT
                d.tournament_id as tourneyid,
                AVG(pr.score) as average_score,
                AVG(opp_pr.score) as average_against
            FROM player_results pr
            JOIN player_results opp_pr
                ON opp_pr.game_id = pr.game_id
               AND opp_pr.player_id != pr.player_id
            JOIN games g ON pr.game_id = g.id
            JOIN divisions d ON g.division_id = d.id
            WHERE pr.player_id = %s
              AND pr.score > 0
            GROUP BY d.tournament_id
        )
        SELECT
            t.id as tourneyid,
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
            tr.new_rating_dev as end_deviation,
            COALESCE(ta.average_score, 0) as average_score,
            COALESCE(ta.average_against, 0) as average_against
        FROM tournament_results tr
        JOIN divisions d ON tr.division_id = d.id
        JOIN tournaments t ON d.tournament_id = t.id
        LEFT JOIN tourney_avgs ta ON ta.tourneyid = t.id
        WHERE tr.player_id = %s
        ORDER BY tr.date DESC
    """
    return execute_query(query, (player_id, player_id))


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
            opp_tr.start_rating as opponent_rating,
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
        JOIN tournament_results opp_tr
            ON opp_tr.player_id = opp_p.id
           AND opp_tr.division_id = d.id
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


def get_peak_rating_last_two_years(player_id: int) -> Optional[int]:
    """Get the highest end_rating from tournaments in the last 2 years."""
    query = """
        SELECT MAX(tr.end_rating) as peak_rating
        FROM tournament_results tr
        JOIN divisions d ON tr.division_id = d.id
        JOIN tournaments t ON d.tournament_id = t.id
        WHERE tr.player_id = %s
          AND tr.end_rating IS NOT NULL
          AND t.end_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    """
    row = execute_query_one(query, (player_id,))
    return row['peak_rating'] if row else None


def get_peak_rating_all_time(player_id: int) -> Optional[int]:
    """Get the highest end_rating from all tournaments."""
    query = """
        SELECT MAX(tr.end_rating) as peak_rating
        FROM tournament_results tr
        WHERE tr.player_id = %s
          AND tr.end_rating IS NOT NULL
    """
    row = execute_query_one(query, (player_id,))
    return row['peak_rating'] if row else None
