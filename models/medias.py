class Movie:
    def __init__(self, title, slug, internal_id, score, last_air_date):
        self.title: str = title
        self.slug: str = slug
        self.internal_id: str = internal_id
        self.score: float = score
        self.last_air_date: str = last_air_date

class TVSerie:
    def __init__(self, title, slug, internal_id, score, last_air_date, seasons) -> None:
        self.title: str = title
        self.slug: str = slug
        self.internal_id: str = internal_id
        self.score: float = score
        self.last_air_date: str = last_air_date
        self.seasons_count: int = seasons

class Season:
    def __init__(self, id, number, episodes):
        self.season_id = id
        self.number = number
        self.episodes_count = episodes

class Episode:
    def __init__(self, id, number, title, duration, plot):
        self.episode_id = id
        self.number = number
        self.title = title
        self.duration = duration
        self.plot = plot