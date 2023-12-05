import requests, json, inquirer, configparser, os, re, webbrowser
from src.display import Ask
from src.downloader import VideoDownloader
from src.m3u8_parser import M3U8PlaylistParser
from models.medias import Movie, TVSerie, Season, Episode
from models.tokens import Token

def get_domain_from_ini(file_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config['DOMAIN']['updated']

class Search:
    def __init__(self, query) -> None:
        self.query = query
        self.result = []

    def search(self):
        api_response = requests.get(f"https://streamingcommunity.{get_domain_from_ini()}/api/search?q={self.query}").json()
        for data in api_response["data"]:
            match data["type"]:
                case "tv":
                    last_air = data["last_air_date"] if data['last_air_date'] else ''
                    self.result.append(TVSerie(title=data['name'], slug=data["slug"], internal_id=data["id"], seasons=data["seasons_count"], score=data["score"], last_air_date=last_air))
                case "movie":
                    last_air = data["last_air_date"] if data['last_air_date'] else ''
                    self.result.append(Movie(title=data['name'], slug=data["slug"], internal_id=data["id"], score=data["score"], last_air_date=last_air))

class StreamingCommunityAPI:
    def __init__(self, solution_query):
        self.headers = {
            'X-Inertia': 'true', 
            'X-Inertia-Version': '20f1d2bdf859760cb5ae6f10e6c94cd2'
        }
        self.domain = get_domain_from_ini()
        self.solution_query = solution_query
        self.content_type = 'tv' if hasattr(solution_query, 'seasons_count') else 'movie'

    def fetch_media_info(self):
        if self.content_type == 'tv':
            return self.get_serie_info()
        elif self.content_type != 'movie':
            return None 

    def get_serie_info(self) -> list:
        response = requests.get(
            f'https://streamingcommunity.{self.domain}/titles/{self.solution_query.internal_id}-{self.solution_query.slug}',
            headers=self.headers
        ).json()
        # da qua possiamo espandere e prendere un sacco di infos sulla serie. Per ora prendiamo solo le stagioni
        seasons_raw =response["props"]["title"]["seasons"]
        seasons = [Season(season["id"], season["number"], season["episodes_count"]) for season in seasons_raw]
        return seasons

    def get_season_info(self, season_index):
        headers = {'X-Inertia-Partial-Component': 'Titles/Title',  'X-Inertia-Partial-Data': 'loadedSeason'}
        response = requests.get(
            f'https://streamingcommunity.{self.domain}/titles/{self.solution_query.internal_id}-{self.solution_query.slug}/stagione-{season_index}',
            headers={**self.headers, **headers},
        )
        # da qua possiamo espandere e prendere un sacco di infos sulla stagione. Ora prendiamo solo gli episodi
        episodes_raw = response.json()["props"]["loadedSeason"]["episodes"]
        episodes = [Episode(episode["id"], episode["number"], episode["name"], episode["duration"], episode["plot"]) for episode in episodes_raw]
        return episodes


    # MARK: both return an iframe
    def get_episode_info(self, episode_id):
        response = requests.get(f'https://streamingcommunity.{self.domain}/watch/{self.solution_query.internal_id}', 
            params={'e': episode_id}, 
            headers=self.headers
        ).json()
        episode_name = f"_S{response['props']['episode']['season']['number']}E{response['props']['episode']['number']}"
        iframe_url = response["props"]["embedUrl"]
        return episode_name, iframe_url

    def get_movie_info(self):
        response = requests.get(
            f'https://streamingcommunity.{self.domain}/watch/{self.solution_query.internal_id}',
            headers=self.headers,
        ).json()
        # da qua possiamo prendere un sacco di infos sul film
        iframe_url = response["props"]["embedUrl"]
        return iframe_url

    @staticmethod
    def get_tokens_from_iframe(url):
        iframe_url = re.findall(r'src="([^"]+)"', requests.get(url).text)[0].replace("&amp;", "&")
        internal_id = re.search(r'https:\/\/vixcloud\.co\/embed\/(\d+)', iframe_url)[1]
        iframe_source = requests.get(iframe_url).content
        iframe_video_infos = re.findall(r'<script>([\s\S]*?)<\/script>', iframe_source.decode())

        if playlist_match := re.search(r'params:\s*\{([\s\S]*?)\}\s*,', str(iframe_video_infos)):
            playlist_match_formatted = playlist_match[0].replace("\\n                \\", '').replace("\\", '').replace("n            ", '').strip()
            params_clean_matches = re.findall(r"'token[0-9a-zA-Z]*':\s*'([^']*)'", playlist_match_formatted)
            exp = re.findall(r"'expires':\s*'([^']*)'", playlist_match_formatted)[0]
            return internal_id, Token(*params_clean_matches, exp)

    @staticmethod
    def get_media_contents(internal_id, tokens):
        uri = f"https://vixcloud.co/playlist/{internal_id}?token={tokens.token}&token480p={tokens.token480p}&token720p={tokens.token720p}&expires={tokens.expire}&b=1"
        parser = M3U8PlaylistParser(requests.get(uri).text)
        parsed_data = parser()
        return parsed_data



def main():
    logo = '''
   _____ __                            ____            __    __     
  / ___// /_________  ____ _____ ___  / __ )__  ______/ /___/ /_  __
  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \/ __  / / / / __  / __  / / / /
 ___/ / /_/ /  /  __/ /_/ / / / / / / /_/ / /_/ / /_/ / /_/ / /_/ / 
/____/\__/_/   \___/\__,_/_/ /_/ /_/_____/\__,_/\__,_/\__,_/\__, /  
                                                           /____/
    '''
    def center(var:str, space:int=None): return '\n'.join(' ' * int(space or (os.get_terminal_size().columns - len(var.splitlines()[len(var.splitlines()) // 2])) / 2) + line for line in var.splitlines())
    print(center(logo))

    ask = Ask()
    query = ask.search_query()
    search_instance = Search(query)
    search_instance.search()

    if search_instance.result: 
        selection = ask.display_search_results(search_instance.result)
    else: print("[ERROR] Non sono stati trovati risultati per la tua ricerca")

    sc = StreamingCommunityAPI(selection)
    infos = sc.fetch_media_info()
    if sc.content_type == "tv":
        selected_season = ask.serie_season(infos)
        s_episodes = sc.get_season_info(selected_season)
        episode = ask.season_espisode(s_episodes)
        episode_title, iframe_url = sc.get_episode_info(episode.episode_id)
        title = f"{selection.title}_{episode_title}"
    else:
        iframe_url = sc.get_movie_info()
        title = selection.title

    internal_id, tokens = sc.get_tokens_from_iframe(iframe_url)
    media = sc.get_media_contents(internal_id, tokens)

    quality_index = ask.display_possible_qualities()
    action = ask.display_possible_actions()
    actions_map = {
        (0,): lambda: perform_download(media, quality_index, sc),
        (1,): lambda: open_web_page(sc),
        (0, 1): lambda: download_and_open_web_page(media, quality_index, sc),
    }
    def perform_download(media, quality_index, sc):
        download_options = {
            "track": media["video_tracks"][quality_index],
            "subtitles": "",
            "track_infos": {
                "id": internal_id,
                "title": title,
            }
        }
        VideoDownloader().download(download_options)

    def open_web_page(sc):
        webbrowser.open(iframe_url)

    def download_and_open_web_page(media, quality_index, sc):
        open_web_page(sc)
        perform_download(media, quality_index, sc)

    actions_map.get(tuple(sorted(action)), lambda: None)()

main()
