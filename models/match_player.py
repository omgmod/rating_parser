from datetime import datetime


class MatchPlayer:
    def __init__(self, name, side, os_rating, ts_rating, last_played):
        self.name = name
        self.side = side
        self.os_rating = os_rating
        self.ts_rating = ts_rating
        self.last_played = last_played

    def weeks_since_last_played(self, now: datetime):
        # First game, don't worry about time gap
        if self.last_played is None:
            return 0

        timedelta = now - self.last_played
        return timedelta.days // 7

    def months_since_last_played(self, now: datetime):
        # First game, don't worry about time gap
        if self.last_played is None:
            return 0

        return (now.year - self.last_played.year) * 12 + now.month - self.last_played.month
