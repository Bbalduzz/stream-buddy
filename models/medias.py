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