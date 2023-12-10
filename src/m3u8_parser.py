import re
from typing import Dict, List

class M3U8PlaylistParser:
    SUB_REGEX = r'LANGUAGE="([^"]+)",URI="([^"]+)"'
    VIDEOS_REGEX = r'#EXT-X-STREAM-INF:[^\n]+\n(https?://[^\n]+)'
    AUDIO_REGEX = r'#EXT-X-MEDIA:TYPE=AUDIO,[^\n]*,LANGUAGE="([^"]+)",URI="([^"]+)"'

    def __init__(self, playlist_content):
        self.playlist_content = playlist_content
        self.audio_tracks = []
        self.video_tracks = []
        self.subtitle_tracks = []

    def parse_playlist(self) -> Dict[str, List]:
        self.audio_tracks = re.findall(self.AUDIO_REGEX, self.playlist_content)
        self.subtitle_tracks = re.findall(self.SUB_REGEX, self.playlist_content)
        self.video_tracks = [track.replace("&b=1", "") for track in re.findall(self.VIDEOS_REGEX, self.playlist_content)]
        return {
            "audio_tracks": self.audio_tracks,
            "subtitle_tracks": self.subtitle_tracks,
            "video_tracks": self.video_tracks
        }

    def __call__(self) -> Dict[str, List]:
        return self.parse_playlist()

