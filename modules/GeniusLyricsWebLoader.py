import dataclasses
from typing import Optional, List, Tuple
import requests
import re
from .LyricsWebLoaderBase import LyricsProvider, LyricsWebLoaderBase
from bs4 import BeautifulSoup
from config import configuration as _conf


@dataclasses.dataclass
class RequestResponseData:
    Artist: str
    Song: str
    GeniusLyricsWebPageUrl: str
    FullTitle: str


class GeniusLyricsWebLoader(LyricsWebLoaderBase):
    def __init__(self):
        self._sourceUrl = r"https://api.genius.com/"

    def RequestLyrics(self, artist: str, song: str) -> bool:
        search_result: Optional[RequestResponseData] = self._makeSearchRequest(f"{artist} {song}")
        if search_result is None:
            return False
        if not self._loadPageContent(search_result.GeniusLyricsWebPageUrl):
            return False
        temp_lyrics: List[Tuple[str, str]] = list()

        lyrics_containers = self._pageContent.findAll("div", attrs={"data-lyrics-container": "true"})

        lines: str = search_result.FullTitle + "\n===============\n"
        for container in lyrics_containers:
            lines += container.text

        for line in lines.split("\n"):
            temp_lyrics.append((line, ""))

        self._lyrics = LyricsProvider(search_result.Artist, search_result.Song, lyrics=temp_lyrics, translated=False, url=search_result.GeniusLyricsWebPageUrl)
        return True

    def _loadPageContent(self, url: str) -> bool:
        resp = requests.get(url)
        if resp.status_code != 200:
            return False
        self._pageContent = BeautifulSoup(resp.text.replace("<br/>", "\n"), "lxml")
        return True

    def _makeSearchRequest(self, request: str) -> Optional[RequestResponseData]:
        json_response = requests.get(f"{self._sourceUrl}search?q={request}&access_token={_conf['genius']['client_access_token']}").json()
        if not json_response["meta"]["status"] == 200:
            return None
        if len(json_response["response"]["hits"]) == 0:
            return None

        most_valuable_result = json_response["response"]["hits"][0]["result"]
        result = RequestResponseData(
            most_valuable_result["title"],
            most_valuable_result["primary_artist"]["name"],
            most_valuable_result["url"],
            most_valuable_result["full_title"]
        )
        return result
