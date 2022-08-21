from abc import ABC as Abstract, abstractmethod
from typing import *

import requests.adapters
from bs4 import BeautifulSoup
import dataclasses
import ssl

_T_File_Descriptor = TypeVar("_T_File_Descriptor", bound=IO, covariant=False, contravariant=True)
_V_Intermediate_Result = TypeVar("_V_Intermediate_Result")


@dataclasses.dataclass
class RequestResponseData:
    Artist: str
    Song: str
    PageUrl: str
    FullTitle: str


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


class LyricsProvider(object):
    def __init__(self, artist: str, song: str, lyrics: Iterable[Tuple[str, str]] = None, translated: bool = False, url: str = None):
        self.__artist = artist
        self.__song = song
        self.__lyrics = list(lyrics)
        self.__translated = translated
        self.__url = url

    __artist: str
    __song: str
    __lyrics: List[Tuple[str, str]]  # original lyrics line - v1, translated - v2
    __translated: bool
    __url: str

    @property
    def Artist(self) -> str:
        return self.__artist

    @property
    def Song(self) -> str:
        return self.__song

    @property
    def Lyrics(self) -> List[Tuple[str, str]]:
        return self.__lyrics

    @property
    def Translated(self) -> bool:
        return self.__translated

    def ExportAsString(self):
        result = ""
        for orig, translate in self.__lyrics:
            result += f"[orig] {orig}\n[tr] {translate}\n\n" if self.__translated else f"{orig}\n"
        if self.__url is not None:
            result += f"\n\n=================\n\nLyrics from: {self.__url}"
        return result

    def ExportToFile(self, path: str) -> None:
        formatted_text = self.ExportAsString()
        with open(path, "w", encoding="utf-8") as file:
            file.write(formatted_text)

    def ExportToFileUnsafe(self, path: str) -> _T_File_Descriptor:
        formatted_text = self.ExportAsString()
        file = open(path, "w+b")
        file.write(formatted_text.encode(encoding="utf-8"))
        return file

    def ExportToByteArray(self) -> bytearray:
        formatted_text = self.ExportAsString()
        return bytearray(formatted_text.encode("utf-8"))

    def __str__(self):
        return self.ExportAsString()


class IntermediateResult:
    _availableUrls: List[RequestResponseData]
    _selection: int

    @property
    def AvailableUrls(self):
        return self._availableUrls

    def __init__(self, urls: List[RequestResponseData]):
        self._availableUrls = urls

    def ConfigureContinue(self, selection: int) -> None:
        if selection not in range(0, len(self._availableUrls) - 1):
            raise IndexError("Selected index not in viable range")
        self._selection = selection

    @property
    def Selection(self) -> Optional[RequestResponseData]:
        return self._availableUrls[self._selection]


class LyricsWebLoaderBase(Abstract):
    _pageContent: BeautifulSoup
    _sourceUrl: str
    _lyrics: LyricsProvider

    @property
    def PageContent(self) -> BeautifulSoup:
        return self._pageContent

    @property
    def SourceUrl(self) -> str:
        return self._sourceUrl

    @SourceUrl.setter
    def SourceUrl(self, value: str):
        self._sourceUrl = value

    @property
    def Lyrics(self) -> LyricsProvider:
        return self._lyrics

    @abstractmethod
    def RequestLyrics(self, artist: str = None, song: str = None, continue_context: IntermediateResult = None) -> bool | _V_Intermediate_Result:
        raise NotImplementedError("Calling abstract method is restricted")

    @abstractmethod
    def _loadPageContent(self, url: str):
        raise NotImplementedError("Calling abstract method is restricted")

    def _validateInput(self, artist: str, song: str) -> None:
        if len(artist) == 0 or len(song) == 0:
            raise BadArgumentException("Song name or artist name has zero value")


class BadArgumentException(Exception):
    pass
