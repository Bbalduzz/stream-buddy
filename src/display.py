import inquirer
from models.medias import Movie, TVSerie

class Ask:
	@staticmethod
	def search_query():
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
	def serie_season(infos):
		seasons = range(1, len(infos) + 1)  # Assuming `infos` contains information about all seasons
		questions = [inquirer.List('season', message="Select a season", choices=seasons)]
		answers = inquirer.prompt(questions)
		return answers['season']

	@staticmethod
	def season_espisode(s_episodes):
		episode_choices = [f"{episode.number}. {episode.title}" for episode in s_episodes]
		questions = [inquirer.List('episode', message="Select an episode", choices=episode_choices)]
		answers = inquirer.prompt(questions)
		# Extracting the episode number from the answer and finding the corresponding episode
		selected_episode_number = int(answers['episode'].split('.')[0])
		selected_episode = next(e for e in s_episodes if e.number == selected_episode_number)
		return selected_episode

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