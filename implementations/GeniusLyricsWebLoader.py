from typing import Optional, List, Tuple
import requests
from base.LyricsWebLoaderBase import LyricsProvider, LyricsWebLoaderBase, IntermediateResult, RequestResponseData
from bs4 import BeautifulSoup
from config import configuration as _conf


class GeniusLyricsWebLoader(LyricsWebLoaderBase):
    def __init__(self):
        self._sourceUrl = r"https://api.genius.com/"

    def RequestLyrics(self, artist: str = None, song: str = None, continue_context: IntermediateResult = None) -> bool | IntermediateResult:
        if continue_context is None:
            intermediate_search_result: Optional[List[RequestResponseData]] = self._makeSearchRequest(f"{artist} {song}")
            if intermediate_search_result is None:
                return False

            return IntermediateResult(intermediate_search_result)
        else:
            search_result = continue_context.Selection
        self._loadPageContent(search_result.PageUrl)
        temp_lyrics: List[Tuple[str, str]] = list()

        lyrics_containers = self._pageContent.findAll("div", attrs={"data-lyrics-container": "true"})

        lines: str = search_result.FullTitle + "\n===============\n"
        for container in lyrics_containers:
            lines += container.text

        for line in lines.split("\n"):
            temp_lyrics.append((line, ""))

        self._lyrics = LyricsProvider(search_result.Artist, search_result.Song, lyrics=temp_lyrics, translated=False,
                                      url=search_result.PageUrl)
        return True

    def _loadPageContent(self, url: str) -> bool:
        resp = requests.get(url)
        if resp.status_code != 200:
            return False
        self._pageContent = BeautifulSoup(resp.text.replace("<br/>", "\n"), "lxml")
        return True

    def _makeSearchRequest(self, request: str) -> Optional[List[RequestResponseData]]:
        json_response = requests.get(f"{self._sourceUrl}search?q={request}&access_token={_conf['genius']['client_access_token']}").json()
        if not json_response["meta"]["status"] == 200:
            return None
        if len(json_response["response"]["hits"]) == 0:
            return None
        valuable_results = json_response["response"]["hits"]

        result: List[RequestResponseData] = list()
        for i in range(0, len(valuable_results) // 2):
            result.append(RequestResponseData(
                valuable_results[i]["result"]["title"],
                valuable_results[i]["result"]["primary_artist"]["name"],
                valuable_results[i]["result"]["url"],
                valuable_results[i]["result"]["full_title"]
            ))
        return result
