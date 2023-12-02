import requests, json, re, inquirer, json, webbrowser, os
from src.m3u8_parser import M3U8PlaylistParser
from src.downloader import VideoDownloader
from models.info import MediaInfos
from models.tokens import Token
from models.medias import Movie, TVSerie

class Search:
	def __init__(self, query) -> None:
		self.query = query
		self.result = []

	def search(self):
		api_response = requests.get(f"https://streamingcommunity.broker/api/search?q={self.query}").json()
		for data in api_response["data"]:
			match data["type"]:
				case "tv":
					if not data['last_air_date']: last_air = ''
					else: last_air = data["last_air_date"]
					self.result.append(TVSerie(title=data['name'], slug=data["slug"], internal_id=data["id"], seasons=data["seasons_count"], score=data["score"], last_air_date=last_air))
				case "movie":
					if not data['last_air_date']: last_air = ''
					else: last_air = data["last_air_date"]
					self.result.append(Movie(title=data['name'], slug=data["slug"], internal_id=data["id"], score=data["score"], last_air_date=last_air))

class StreamingCommunityGrabber:
	def __init__(self, raw_media_id = None):
		self.raw_media_id = raw_media_id
		self.domain = "broker"

	def initialize(self):
		iframe_elem = requests.get(f"https://streamingcommunity.{self.domain}/iframe/{self.raw_media_id}")
		iframe_url = re.findall(r'src="([^"]+)"', iframe_elem.text)[0].replace("&amp;", "&")
		iframe_source = requests.get(iframe_url).content
		self.iframe_video_infos = re.findall(r'<script>([\s\S]*?)<\/script>', iframe_source.decode())
	
	def get_media_infos(self) -> MediaInfos:
		video_regex = r'window\.video\s*=\s*({.*?});'

		if video_match := re.search(video_regex, str(self.iframe_video_infos)):
			video_data = json.loads(video_match[1])
			self.media_infos = MediaInfos(video_data["id"], video_data["name"], video_data["duration"])

		return None
	
	def get_tokens(self) -> Token:
		playlist_regex = r'params:\s*\{([\s\S]*?)\}\s*,'

		if playlist_match := re.search(playlist_regex, str(self.iframe_video_infos)):
			playlist_match_formatted = playlist_match[0].replace("\\n                \\", '').replace("\\", '').replace("n            ", '').strip()
			params_clean_matches = re.findall(r"'token[0-9a-zA-Z]*':\s*'([^']*)'", playlist_match_formatted)
			exp = re.findall(r"'expires':\s*'([^']*)'", playlist_match_formatted)[0]
			self.tokens = Token(*params_clean_matches, exp)

		return None

	def get_media_contents(self):
		uri = f"https://vixcloud.co/playlist/{self.media_infos.internal_id}?token={self.tokens.token}&token480p={self.tokens.token480p}&token720p={self.tokens.token720p}&expires={self.tokens.expire}&b=1"
		parser = M3U8PlaylistParser(requests.get(uri).text)
		parsed_data = parser()
		return parsed_data

	def run(self):
		self.initialize()
		self.get_tokens()
		self.get_media_infos()


class Ask:
	@staticmethod
	def get_search_query():
		questions = [inquirer.Text('query', message="Che cosa vuoi guardare?")]
		answers = inquirer.prompt(questions)
		return answers['query']

	@staticmethod
	def display_search_results(search_results):
		# Calculate the maximum length for each column
		max_title_length = max(len(content.title) for content in search_results)
		max_type_length = max(len('TV Series' if isinstance(content, TVSerie) else 'Movie') for content in search_results)
		max_score_length = max(len(str(content.score)) for content in search_results)
		max_date_length = max(len(content.last_air_date) for content in search_results if content)

		# Construct each row
		choices = []
		for content in search_results:
			content_type = 'TV Series' if isinstance(content, TVSerie) else 'Movie'
			row = f"| {content.title.ljust(max_title_length)} [ {content_type.ljust(max_type_length)} ][ {str(content.score).ljust(max_score_length)} ][ {content.last_air_date.ljust(max_date_length)} ]"
			choices.append(row)

		questions = [inquirer.List('selection', message="Seleziona un contenuto", choices=choices)]
		answers = inquirer.prompt(questions)
		selected_row = answers['selection']

		# Find the selected content object
		for content in search_results:
			content_type = 'TV Series' if isinstance(content, TVSerie) else 'Movie'
			row = f"| {content.title.ljust(max_title_length)} [ {content_type.ljust(max_type_length)} ][ {str(content.score).ljust(max_score_length)} ][ {content.last_air_date.ljust(max_date_length)} ]"
			if row == selected_row:
				return content

	@staticmethod
	def display_possible_qualities():
		choices = ["720p", "480p"]
		questions = [inquirer.List('selection', message="Seleziona la qualità desiderata", choices=choices)]
		answers = inquirer.prompt(questions)
		return choices.index(answers['selection'])

	@staticmethod
	def display_possible_actions():
		choices = ["download", "watch"]
		questions = [inquirer.Checkbox('selections', message="Cosa vuoi fare", choices=choices)]
		answers = inquirer.prompt(questions)
		selected_qualities = answers['selections']
		return [choices.index(quality) for quality in selected_qualities]

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
	query = ask.get_search_query()
	search_instance = Search(query)
	search_instance.search()

	if search_instance.result: selection = ask.display_search_results(search_instance.result)
	else: print("[ERROR] Non sono stati trovati risultati per la tua ricerca")

	sc = StreamingCommunityGrabber(selection.internal_id)
	sc.run()
	media = sc.get_media_contents()

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
			"track_infos": sc.media_infos
		}
		VideoDownloader().download(download_options)

	def open_web_page(sc):
		webbrowser.open(f"https://streamingcommunity.{sc.domain}/iframe/{sc.raw_media_id}")

	def download_and_open_web_page(media, quality_index, sc):
		open_web_page(sc)
		perform_download(media, quality_index, sc)

	actions_map.get(tuple(sorted(action)), lambda: None)()


main()