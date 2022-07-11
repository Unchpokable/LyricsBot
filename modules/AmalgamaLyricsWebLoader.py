from .LyricsWebLoaderBase import LyricsWebLoaderBase, LyricsProvider
from bs4 import BeautifulSoup
from typing import *
import requests
import string
import re


class AmalgamaLyricsWebLoader(LyricsWebLoaderBase):
    def __init__(self):
        self._sourceUrl = r'https://www.amalgama-lab.com/songs/'

    def RequestLyrics(self, artist: str, song: str) -> bool:
        final_url = self._formatUrl(artist, song)
        if not self._loadPageContent(final_url):
            return False
        lines = self._pageContent.findAll("div", class_="string_container")
        temp_lyrics: List[Tuple[str, str]] = list()
        for line in lines:
            orig = line.find("div", class_="original")
            translate = line.find("div", class_="translate")
            if orig.find("strong") or translate.find("strong"):  # Если встречаем жирный текст, значит на странице несколько переводов и это - заголовок следующего. <h1></h1> для слабаков
                break
            temp_lyrics.append((orig.text, translate.text))
        self._lyrics = LyricsProvider(artist, song, temp_lyrics, translated=True, url=final_url)
        return True

    def _formatUrl(self, artist: str, song: str) -> str:
        self._validateInput(artist, song)
        _artist = re.sub(rf"[{string.punctuation}\' +]", "_", artist)
        _song = re.sub(rf"[{string.punctuation}\' +]", "_", song)
        return self._sourceUrl + fr"{_artist[0].lower()}/{_artist.lower()}/{_song.lower()}.html"

    def _loadPageContent(self, url: str) -> bool:
        resp = requests.get(url)
        if resp.status_code != 200:
            return False
        # Костыль, т.к при ошибке в названии песни или исполнителя, или если перевода нет на сайте, сайт вместо ошибки отображает валидный html с сообщением
        if "Извините, запрашиваемый документ не найден или не существует. Попробуйте воспользоваться нашим поиском!" in resp:
            return False
        self._pageContent = BeautifulSoup(resp.text, "lxml")
        return True

