import dataclasses
import io

import requests.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from config import configuration as _conf
from modloader import ModuleLoader
from base import LyricsWebLoaderBase, LyricsProvider, IntermediateResult
from typing import *
import inspect
import logging


@dataclasses.dataclass
class UserRequest:
    Artist: str
    Song: str
    MessageID: int
    UserID: int
    ExtendedDialog: bool = False
    AssignedSearcher: LyricsWebLoaderBase = None
    IntermediateRequestResult: IntermediateResult = None


_bot = Bot(_conf["telegram"]["bot_token"])
_dispatcher = Dispatcher(_bot)

logging.basicConfig(level=logging.INFO)

_modules = ModuleLoader(lambda cls: issubclass(cls, LyricsWebLoaderBase) and not inspect.isabstract(cls),
                        auto_instantiate=False).Load("implementations")
_activeSessions: Dict[int, UserRequest] = {}


@_dispatcher.message_handler(commands="debug-show-sessions")
async def Debug_ShowSessions(msg: types.Message):
    await msg.answer(str(_activeSessions))


@_dispatcher.message_handler(commands="lyrics")
async def RegisterUserRequest(msg: types.Message):
    artist, song = msg.text.lower().replace("/lyrics", "").split("-")
    result = await msg.answer(f"Select search engine:\n", reply_markup=CreateSearchersSelectKeyboard())
    request = UserRequest(artist.strip(), song.strip(), result.message_id, msg.from_id)
    _activeSessions[msg.from_id] = request
    logging.info(f"Session created: {msg.from_id} with request: {request}")
    return


@_dispatcher.message_handler(lambda msg: msg.text in _conf["searchers"] and msg.from_id in _activeSessions.keys())
async def SearchLyrics(msg: types.Message):
    request: UserRequest = _activeSessions[msg.from_id]
    searcher: LyricsWebLoaderBase = _modules[_conf["searchers"][msg.text]]()
    _activeSessions[msg.from_id].AssignedSearcher = searcher
    await msg.answer("searching...", reply_markup=ReplyKeyboardRemove())
    try:
        request_result = searcher.RequestLyrics(request.Artist, request.Song)
    except requests.exceptions.SSLError as e:
        await msg.answer("Sorry, but looks like requested host unable to accept network requests at this time. You can try later or choose another search engine")
        del _activeSessions[msg.from_id]
        return

    if not request_result:
        await msg.answer("Sorry, nothing was found. Check that you spelled song title and artist name correctly")
        del _activeSessions[msg.from_id]
        return

    if isinstance(request_result, IntermediateResult):
        text, reply_keyboard = FormatSearchList(request_result)
        await msg.answer(f"Top results:\n\n{text}", reply_markup=reply_keyboard)
        _activeSessions[msg.from_id].ExtendedDialog = True
        _activeSessions[msg.from_id].IntermediateRequestResult = request_result
        return

    await ReplyLyrics(msg, searcher.Lyrics)

    del _activeSessions[msg.from_id]
    logging.info(f"Session removed: {msg.from_id}")
    return


@_dispatcher.message_handler(lambda msg: msg.from_id in _activeSessions.keys() and
                             _activeSessions[msg.from_id].ExtendedDialog)
async def ContinueSearch(msg: types.Message):
    index = int(msg.text[0]) - 1
    _activeSessions[msg.from_id].IntermediateRequestResult.ConfigureContinue(index)
    final_result = _activeSessions[msg.from_id].AssignedSearcher.RequestLyrics(continue_context=_activeSessions[msg.from_id].IntermediateRequestResult)
    if not final_result:
        await msg.reply("Sorry, but something went wrong. Please, try again")
        return
    await ReplyLyrics(msg, _activeSessions[msg.from_id].AssignedSearcher.Lyrics)


async def ReplyLyrics(msg: types.Message, lyrics: LyricsProvider):
    if lyrics is None:
        await msg.answer("Technical issue: search engine returned empty lyrics")

    result = ""
    line_count = 0
    for line in lyrics.ExportAsString().split("\n"):
        result += f"{line}\n"
        line_count += 1
        if line_count >= 30:
            await msg.answer(result)
            line_count = 0
            result = ""
    await msg.answer(result, reply_markup=ReplyKeyboardRemove())


def CreateSearchersSelectKeyboard() -> ReplyKeyboardMarkup:
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for searcher, _ in _conf["searchers"].items():
        keyboard_markup.add(KeyboardButton(searcher))
    return keyboard_markup


def FormatSearchList(viable_answers: IntermediateResult) -> Tuple[str, ReplyKeyboardMarkup]:
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    text = ""
    for index, request_response in enumerate(viable_answers.AvailableUrls):
        line = f'{index + 1}. {request_response.Artist} - {request_response.Song}\n'
        keyboard_markup.add(line)
        text += line
    return text, keyboard_markup


if __name__ == "__main__":
    executor.start_polling(_dispatcher, skip_updates=True)
