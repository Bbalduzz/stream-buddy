class Token:
	def __init__(self, token = None, token360p = None, token480p = None, token720p = None, token1080p = None, expiration = None) -> None:
		self.token = token
		self.token360p = token360p
		self.token480p = token480p
		self.token720p = token720p
		self.token1080p = token1080p
		self.expire = expiration