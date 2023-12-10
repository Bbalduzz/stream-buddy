import requests, json, inquirer, configparser, os, re, webbrowser, concurrent.futures, signal
from flask import Flask, render_template, request
from src.display import Ask
from src.downloader import VideoDownloader
from src.m3u8_parser import M3U8PlaylistParser
from src.utils import get_domain_from_ini, versioning_control
from models.medias import Movie, TVSerie, Season, Episode
from models.tokens import Token

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
        self.domain = get_domain_from_ini()
        self.headers = {
            'X-Inertia': 'true', 
            'X-Inertia-Version': json.loads(re.findall(r'data-page="([^"]+)"', requests.get(f"https://streamingcommunity.{self.domain}/").text)[0].replace("&quot;", '"'))["version"]
        }
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

    def get_media_contents(self, internal_id, tokens):
        self.master_uri = f"https://vixcloud.co/playlist/{internal_id}?token={tokens.token}&token480p={tokens.token480p}&token720p={tokens.token720p}&expires={tokens.expire}&b=1"
        parser = M3U8PlaylistParser(requests.get(self.master_uri).text)
        parsed_data = parser()
        return parsed_data



def main():
    logo = f'''
   _____ __                            ____            __    __     
  / ___// /_________  ____ _____ ___  / __ )__  ______/ /___/ /_  __
  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \/ __  / / / / __  / __  / / / /
 ___/ / /_/ /  /  __/ /_/ / / / / / / /_/ / /_/ / /_/ / /_/ / /_/ / 
/____/\__/_/   \___/\__,_/_/ /_/ /_/_____/\__,_/\__,_/\__,_/\__, / 
.{get_domain_from_ini() + " "*(58-len(get_domain_from_ini()))}/____/ 
    '''
    def center(var:str, space:int=None): return '\n'.join(' ' * int(space or (os.get_terminal_size().columns - len(var.splitlines()[len(var.splitlines()) // 2])) / 2) + line for line in var.splitlines())
    print(center(logo))

    versioning_control()

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
        (0,): lambda: perform_download(media, quality_index),
        (1,): lambda: open_web_page(),
        (0, 1): lambda: download_and_open_web_page(media, quality_index),
    }
    def perform_download(media, quality_index):
        download_options = {
            "track": media["video_tracks"][quality_index],
            "subtitles": "",
            "track_infos": {
                "id": internal_id,
                "title": title,
            }
        }
        VideoDownloader().download(download_options)

    def open_web_page():
        def run_app():
            app = Flask(__name__)
            @app.route('/shutdown', methods=['POST'])
            def shutdown_flask_app():
                return os.kill(os.getpid(), signal.SIGTERM)
            @app.route('/')
            def render_html():
                html_content = f'''
                                <!DOCTYPE html>
                <html>
                <head>
                    <title>StreamBuddy player</title>
                    <link rel="stylesheet" href="https://unpkg.com/plyr@3/dist/plyr.css"/>
                </head>
                <style>
                    html, body {{
                        margin: 0;
                        padding: 0;
                        height: 100%;
                        background: #121212;
                        font-family: sans-serif;
                        font-weight: 300;
                    }}
                    .overlay {{
                        text-align: left;
                        position: absolute;
                        color:white;
                        margin-left: 20px;
                        opacity: 1; /* initially visible */
                        transition: opacity 0.5s ease;
                        top: 0;
                        left: 0;
                        right: 0;
                        z-index: 999;
                        pointer-events: none;
                    }}
                    .container {{
                        height: 100vh;
                    }}
                    .plyr {{
                        border-radius: 4px;
                        height: 100%;
                    }}
                </style>
                <body>
                    <div class="overlay"><h1>{title}</h1></div>
                    <div class="container">
                        <video controls crossorigin playsinline></video>
                    </div>
                    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                    <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
                </body>
                <script>
                document.addEventListener('DOMContentLoaded', function () {{
                    var video = document.querySelector('video');
                    var videoSrc = '{sc.master_uri}';

                    const controls = ['play-large', 'rewind', 'play', 'fast-forward', 'progress', 'current-time','duration', 'mute','volume','captions', 'settings', 'fullscreen'];
                    
                    // captions.update is required for captions to work with hls.js
                    const player = new Plyr(video, {{controls, title: "{title}", captions: {{update: true}}}});
                    var overlay = document.querySelector(".overlay")
                    var timeout;
                    function hideOverlay() {{overlay.style.opacity = '0';}}
                    function resetOverlayTimeout() {{
                        clearTimeout(timeout); // clear existing timeout
                        overlay.style.opacity = '1'; // show overlay
                        timeout = setTimeout(hideOverlay, 2000); // hide overlay after 2 seconds
                    }}
                    // Reset the overlay disappearance timeout on video events
                    video.addEventListener('play', resetOverlayTimeout);
                    video.addEventListener('pause', resetOverlayTimeout);
                    video.addEventListener('seeked', resetOverlayTimeout);
                    video.addEventListener('mouseenter', resetOverlayTimeout);
                    video.addEventListener('mouseleave', function() {{
                        timeout = setTimeout(hideOverlay, 300);
                    }});

                    if (Hls.isSupported()) {{
                        var hls = new Hls();
                        hls.loadSource(videoSrc);
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, function () {{
                            video.play();
                        }});
                    }}
                    // HLS.js is not supported on platforms that do not have Media Source Extensions (MSE) enabled.
                    // When the browser has built-in HLS support (check using `canPlayType`), we can provide an HLS manifest (i.e. .m3u8 URL) directly to the video element through the `src` attribute.
                    else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                        video.src = videoSrc;
                        video.addEventListener('loadedmetadata', function () {{
                            video.play();
                        }});
                    }}
                }});

                // to detect the closure of the player
                window.onbeforeunload = function() {{
                    navigator.sendBeacon('http://127.0.0.1:5000/shutdown');
                }};
                </script>
                </html>
                '''
                return html_content

            app.run(port=5001, host='0.0.0.0', threaded=True)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_app)
            webbrowser.open("http://127.0.0.1:5001")
            # se vuoi guardare il contenuto su un altro dispositivo assicurati che sia condivida la rete network con questo dispositivo
            # poi copia nel motore di ricerca l'indirizzo IP pubblico della tua rete seguito da :5001
            # LO VEDI ANCHE DALLA CONSOLE:
            #  * Running on all addresses (0.0.0.0)
            #  * Running on http://127.0.0.1:5001    <-- attuale
            #  * Running on http://192.168.1.3:5001  <-- per accedere da un altro dispositivo


    def download_and_open_web_page(media, quality_index):
        open_web_page()
        perform_download(media, quality_index)

    actions_map.get(tuple(sorted(action)), lambda: None)()

main()
