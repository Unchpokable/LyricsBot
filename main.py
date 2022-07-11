import dataclasses
import io
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from config import configuration as _conf
from modloader import ModuleLoader
from modules import LyricsWebLoaderBase, LyricsProvider
from typing import *
import inspect
import logging


@dataclasses.dataclass
class UserRequest:
    Artist: str
    Song: str
    MessageID: int
    UserID: int


_bot = Bot(_conf["telegram"]["bot_token"])
_dispatcher = Dispatcher(_bot)

logging.basicConfig(level=logging.INFO)

_modules = ModuleLoader(lambda cls: issubclass(cls, LyricsWebLoaderBase) and not inspect.isabstract(cls)).Load("modules")
_activeSessions: Dict[int, UserRequest] = {}


@_dispatcher.message_handler(commands="debug-show-sessions")
async def Debug_ShowSessions(msg: types.Message):
    await msg.answer(str(_activeSessions))


@_dispatcher.message_handler(commands="lyrics")
async def RegisterUserRequest(msg: types.Message):
    artist, song = msg.text.lower().replace("/lyrics", "").split("-")
    result = await msg.answer("What searcher engine i should use for you?", reply_markup=CreateSearchersSelectKeyboard())
    request = UserRequest(artist.strip(), song.strip(), result.message_id, msg.from_id)
    _activeSessions[msg.from_id] = request
    return


@_dispatcher.message_handler(lambda msg: msg.text in _conf["searchers"] and msg.from_id in _activeSessions.keys())
async def SearchLyrics(msg: types.Message):
    request: UserRequest = _activeSessions[msg.from_id]
    searcher: LyricsWebLoaderBase = _modules[_conf["searchers"][msg.text]]
    if not searcher.RequestLyrics(request.Artist, request.Song):
        await msg.answer("Sorry, nothing was found. Check that you spelled song title and artist name correctly")
        del _activeSessions[msg.from_id]
        return
    file = f"{request.Artist} - {request.Song}.txt"
    bin_file = searcher.Lyrics.ExportToByteArray()
    await msg.answer_document(types.InputFile(io.BytesIO(bin_file), filename=file))
    await _bot.delete_message(_activeSessions[msg.from_id].UserID, _activeSessions[msg.from_id].MessageID)
    del _activeSessions[msg.from_id]
    return


def CreateSearchersSelectKeyboard() -> ReplyKeyboardMarkup:
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for searcher, _ in _conf["searchers"].items():
        keyboard_markup.add(KeyboardButton(searcher))
    return keyboard_markup


if __name__ == "__main__":
    executor.start_polling(_dispatcher, skip_updates=True)
