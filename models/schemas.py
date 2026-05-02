from typing import Optional, List, Dict, Any
from datetime import date


class TournamentResult:
    def __init__(self, data: Dict[str, Any]):
        self.tourneyid = data.get('tourneyid')
        self.name = data.get('name')
        self.date = data.get('date')
        self.division = data.get('division')
        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.ties = data.get('ties', 0)
        self.place = data.get('place')
        self.totalplayers = data.get('totalplayers')
        self.rating = data.get('rating')
        self.ratingchange = data.get('ratingchange')
        self.points = data.get('points')
        self.averagepoints = data.get('averagepoints')

    def to_dict(self):
        return {
            'tourneyid': self.tourneyid,
            'name': self.name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'division': self.division,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'place': self.place,
            'totalplayers': self.totalplayers,
            'rating': self.rating,
            'ratingchange': self.ratingchange,
            'points': self.points,
            'averagepoints': self.averagepoints
        }


class CrossTablesPlayer:
    def __init__(self, data: Dict[str, Any]):
        self.playerid = data.get('playerid')
        self.name = data.get('name')
        self.cswrating = data.get('cswrating')
        self.cswranking = data.get('cswranking')
        self.twlrating = None  # Always null per spec
        self.twlranking = None  # Always null per spec
        self.w = data.get('wins', 0)
        self.l = data.get('losses', 0)
        self.t = data.get('ties', 0)
        self.b = data.get('byes', 0)
        self.photourl = data.get('photourl')
        self.city = None  # Not available
        self.state = None  # Not available
        self.country = data.get('country')
        self.tournamentCount = data.get('tournament_count')
        self.averageScore = data.get('average_score')
        self.opponentAverageScore = data.get('opponent_average_score')
        self.results = []

    def to_dict(self, include_results=False):
        result = {
            'playerid': self.playerid,
            'name': self.name,
            'twlrating': self.twlrating,
            'cswrating': self.cswrating,
            'twlranking': self.twlranking,
            'cswranking': self.cswranking,
            'w': int(self.w) if self.w is not None else 0,
            'l': int(self.l) if self.l is not None else 0,
            't': int(self.t) if self.t is not None else 0,
            'b': int(self.b) if self.b is not None else 0,
            'photourl': self.photourl,
            'city': self.city,
            'state': self.state,
            'country': self.country
        }

        if include_results:
            result.update({
                'tournamentCount': self.tournamentCount,
                'averageScore': float(self.averageScore) if self.averageScore else None,
                'opponentAverageScore': float(self.opponentAverageScore) if self.opponentAverageScore else None,
                'results': [r.to_dict() for r in self.results]
            })

        return result


class HeadToHeadGame:
    def __init__(self, data: Dict[str, Any]):
        self.gameid = data.get('gameid')
        self.date = data.get('date')
        self.tourneyname = data.get('tourneyname')
        self.player1 = {
            'playerid': data.get('player1_id'),
            'name': data.get('player1_name'),
            'score': data.get('player1_score'),
            'oldrating': data.get('player1_oldrating'),
            'newrating': data.get('player1_newrating'),
            'position': data.get('player1_position')
        }
        self.player2 = {
            'playerid': data.get('player2_id'),
            'name': data.get('player2_name'),
            'score': data.get('player2_score'),
            'oldrating': data.get('player2_oldrating'),
            'newrating': data.get('player2_newrating'),
            'position': data.get('player2_position')
        }
        self.annotated = data.get('annotated')

    def to_dict(self):
        return {
            'gameid': self.gameid,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'tourneyname': self.tourneyname,
            'player1': self.player1,
            'player2': self.player2,
            'annotated': self.annotated
        }


class HeadToHeadResult:
    """Result row from a head-to-head game in its raw form."""
    def __init__(self, data: Dict[str, Any]):
        self.gameid = data.get('gameid')
        self.date = data.get('date')
        self.tourneyname = data.get('tourneyname')
        self.player1_id = data.get('player1_id')
        self.player1_name = data.get('player1_name')
        self.player1_score = data.get('player1_score')
        self.player2_id = data.get('player2_id')
        self.player2_name = data.get('player2_name')
        self.player2_score = data.get('player2_score')


class PlayerStatsV2:
    """Detailed aggregated stats for a player's career."""

    def __init__(self, data: Dict[str, Any]):
        self.gamesPlayed = data.get('gamesPlayed', 0)
        self.wins = data.get('wins', 0)
        self.losses = data.get('losses', 0)
        self.draws = data.get('draws', 0)
        self.byes = data.get('byes', 0)
        self.winPercentage = data.get('winPercentage', 0.0)
        self.averageScore = data.get('averageScore', 0.0)
        self.averageAgainst = data.get('averageAgainst', 0.0)
        self.highGame = data.get('highGame')
        self.highGameOpponent = data.get('highGameOpponent')
        self.lowGame = data.get('lowGame')
        self.lowGameOpponent = data.get('lowGameOpponent')
        self.biggestWin = data.get('biggestWin')
        self.biggestWinOpponent = data.get('biggestWinOpponent')
        self.highLoss = data.get('highLoss')
        self.highLossOpponent = data.get('highLossOpponent')
        self.lowWin = data.get('lowWin')
        self.lowWinOpponent = data.get('lowWinOpponent')
        self.gamesUnder300 = data.get('gamesUnder300', 0)
        self.games300to399 = data.get('games300to399', 0)
        self.games400to499 = data.get('games400to499', 0)
        self.games500to599 = data.get('games500to599', 0)
        self.games600plus = data.get('games600plus', 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'gamesPlayed': self.gamesPlayed,
            'wins': self.wins,
            'losses': self.losses,
            'draws': self.draws,
            'byes': self.byes,
            'winPercentage': round(self.winPercentage, 2),
            'averageScore': round(self.averageScore, 2),
            'averageAgainst': round(self.averageAgainst, 2),
            'highGame': self.highGame,
            'highGameOpponent': self.highGameOpponent,
            'lowGame': self.lowGame,
            'lowGameOpponent': self.lowGameOpponent,
            'biggestWin': self.biggestWin,
            'biggestWinOpponent': self.biggestWinOpponent,
            'highLoss': self.highLoss,
            'highLossOpponent': self.highLossOpponent,
            'lowWin': self.lowWin,
            'lowWinOpponent': self.lowWinOpponent,
            'gamesUnder300': self.gamesUnder300,
            'games300to399': self.games300to399,
            'games400to499': self.games400to499,
            'games500to599': self.games500to599,
            'games600plus': self.games600plus,
        }


class TournamentRoundResult:
    """A single round within a tournament for a player."""

    def __init__(self, data: Dict[str, Any]):
        self.round = data.get('round')
        self.opponent_name = data.get('opponent_name')
        self.opponent_id = data.get('opponent_id')
        self.opponent_rating = data.get('opponent_rating')
        self.result = data.get('result')  # 'W', 'L', 'D', 'B'
        self.score_for = data.get('score_for')
        self.score_against = data.get('score_against')
        self.player_rating_at_time = data.get('player_rating_at_time')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'round': self.round,
            'opponent_name': self.opponent_name,
            'opponent_id': self.opponent_id,
            'opponent_rating': self.opponent_rating,
            'result': self.result,
            'score_for': self.score_for,
            'score_against': self.score_against,
            'player_rating_at_time': self.player_rating_at_time,
        }


class TournamentResultDetailV2:
    """A tournament entry in a player's history with per-round detail."""

    def __init__(self, data: Dict[str, Any]):
        self.playerid = data.get('playerid')
        self.tourneyid = data.get('tourneyid')
        self.name = data.get('name')
        self.date = data.get('date')
        self.division = data.get('division')
        self.rounds: List[TournamentRoundResult] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'playerid': self.playerid,
            'tourneyid': self.tourneyid,
            'name': self.name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'division': self.division,
            'rounds': [r.to_dict() for r in self.rounds],
        }


class TournamentListItemV2:
    """A tournament entry as it appears in the player endpoint's tournaments list."""

    def __init__(self, data: Dict[str, Any]):
        self.tourneyid = data.get('tourneyid')
        self.name = data.get('name')
        self.date = data.get('date')
        self.division = data.get('division')
        self.wins = data.get('wins')
        self.losses = data.get('losses')
        self.draws = data.get('draws', 0)
        self.spread = data.get('spread', 0)
        self.place = data.get('place')
        self.endRating = data.get('end_rating')
        self.ratingChange = data.get('rating_change')
        self.startDeviation = data.get('start_deviation')
        self.endDeviation = data.get('end_deviation')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tourneyid': self.tourneyid,
            'name': self.name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'division': self.division,
            'wins': int(self.wins) if self.wins is not None else 0,
            'losses': int(self.losses) if self.losses is not None else 0,
            'draws': int(self.draws) if self.draws is not None else 0,
            'spread': int(self.spread) if self.spread is not None else 0,
            'place': self.place,
            'endRating': self.endRating,
            'ratingChange': self.ratingChange,
            'startDeviation': self.startDeviation,
            'endDeviation': self.endDeviation,
        }


class PlayerResponseV2:
    """Top-level v2 player response."""

    def __init__(self, data: Dict[str, Any]):
        self.playerid = data.get('playerid')
        self.name = data.get('name')
        self.country = data.get('country')
        self.cswrating = data.get('cswrating')
        self.photourl = data.get('photourl')
        self.stats: Optional[PlayerStatsV2] = None
        self.tournaments: List[TournamentListItemV2] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'playerid': self.playerid,
            'name': self.name,
            'country': self.country,
            'cswrating': self.cswrating,
            'photourl': self.photourl,
            'stats': self.stats.to_dict() if self.stats else None,
            'tournaments': [t.to_dict() for t in self.tournaments],
        }
