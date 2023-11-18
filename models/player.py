from datetime import datetime


class Player:
    def __init__(self, name, os_rating, ts_rating):
        self.name = name
        self.os_rating = os_rating
        self.ts_rating = ts_rating
        self.last_played = None
        self.games_played = 0
        self.wins = 0
        self.losses = 0

    def update_os_rating(self, os_rating, last_played: datetime):
        self.os_rating = os_rating
        self.last_played = last_played

    def update_ts_rating(self, ts_rating):
        self.ts_rating = ts_rating

    def update_win_loss(self, is_win):
        self.wins += 1 if is_win else 0
        self.losses += 1 if not is_win else 0
        self.games_played += 1

    def __repr__(self) -> str:
        return (f"Player(name={self.name}, games_played={self.games_played}, "
                f"wins={self.wins}, losses={self.losses}, "
                f"last_played={self.last_played.strftime('%Y-%m-%d')}, "
                f"os_mu={self.os_rating.mu}, os_sigma={self.os_rating.sigma}, os_rank={self.os_rating.ordinal()}, "
                f"ts_mu={self.ts_rating.mu}, ts_sigma={self.ts_rating.sigma})")

    def __str__(self) -> str:
        return (
            f"Player: \n\n"
            f"name: {self.name}\n"
            f"games_played: {self.games_played}\n"
            f"wins: {self.wins}\n"
            f"losses: {self.losses}\n"
            f"last_played: {self.last_played.strftime('%Y-%m-%d')}\n"
            f"os_mu: {self.os_rating.mu}\n"
            f"os_sigma: {self.os_rating.sigma}\n"
            f"os_rank: {self.os_rating.ordinal()}\n"
            f"ts_mu: {self.ts_rating.mu}\n"
            f"ts_sigma: {self.ts_rating.sigma}\n"
        )
