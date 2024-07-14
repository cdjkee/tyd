#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.
# v.1.34

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Dict

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PicklePersistence,
    filters,
)
from telegram.constants import ParseMode
from pytubefix import YouTube
from pytubefix.cli import on_progress
from typing import Final
import threading
import re
import os

# From ENV 
# TOKEN - TG bot token
# soid is a list of TG ids separated with commas to send special messages to
TOKEN = os.environ.get('TOKEN')
soid = os.environ.get('SOID')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# yt_link_reg is regexp to detect valid link in a message
# yt_link_reg_clean is regexp to get a clean link from the message
yt_link_reg: Final = re.compile(r"https://(www\.youtube\.com\/watch\?v\=|youtu\.be/|youtube\.com/shorts/|www\.youtube\.com/shorts/|www\.youtube\.com/live/).*")
yt_link_reg_clean: Final = re.compile(r"https://(www\.youtube\.com\/watch\?v\=|youtu\.be/|youtube\.com/shorts/|www\.youtube\.com/shorts/|www\.youtube\.com/live/).*(\?|$|\s)")
reply_keyboard = [["Download", "Cancel"]]
links_kbd=[]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
threads=[]


#start command handler and entry point for conversation handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation, display any stored data and ask user for input."""
    reply_text = 'Send me a link to youtube video.'
    await update.message.reply_text(reply_text)  
    

#show data command handler
async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(
        f'User_data: {facts_to_str(context.user_data)}'
    )
#cancel command handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    current_jobs = context.job_queue.get_jobs_by_name(context._user_id)
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text('Cache clearead.\n/start to start again.')
    
#help command handler
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text =  'To initiate bot send /start (just click on it)\nThen send a link to youtube.\nBoth "youtu.be" and "www.youtube.com" are supported\nAnd leave "https://" as it is.\nIf you want to stop bot - type /cancel'
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())

#converts data from user_data to readable view
def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

#makes the download link(keyoboard layout for InLineMarkup) with pytube lib and stores it in user_data
def generate_url(context: ContextTypes.DEFAULT_TYPE, link, msg_id) -> int:
    yt = YouTube(link)
    try:
        yt.check_availability()
    except:
        context.user_data[msg_id] = [[InlineKeyboardButton(text=f"Video is unavailable", url=link)]]
    else:
    # context.user_data[msg_id]=generate_msg(yt)
        context.user_data[msg_id] = generate_kbd(yt)
    print("Answer generated and stored")
#outdated 
def generate_msg(yt):
    msg=''
    for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
        msg+=f'\n----------<a href="{stream.url}">Download {stream.resolution} {round(stream.filesize_mb,1)}MB video </a>\n----------'
    print('LINK LIST GENERATED')
    yt.streams.index(   )
    return msg

#generates keyboard layout with buttons with links
def generate_kbd(yt):
    result=[]
    audiorow=[]
    for stream in yt.streams.filter(progressive=True):
        result.append([InlineKeyboardButton(text=f"Download {stream.resolution} {round(stream.filesize_mb,1)}MB video", url=stream.url)])
    
    for stream in yt.streams.filter(only_audio=True):
        audiorow.append(InlineKeyboardButton(text=f"{round(stream.filesize_mb)}MB", url=stream.url))

    result.append(audiorow)
    print('KEYBOARD GENERATED')
    return result

#function for the JOB which detects if link generated
async def check_status(context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data:
        return 0
    
    msg_id, kbd = context.user_data.popitem()
    markup = InlineKeyboardMarkup(kbd)
    await context.bot.send_message(
            # chat_id = context._user_id, text='links plz', parse_mode=ParseMode.HTML, reply_to_message_id=msg_id, reply_markup=answer
            chat_id = context._user_id, text='links are valid for a few hours. Last row contains audio only', reply_to_message_id=msg_id, reply_markup=markup
        )
    
    context.job.schedule_removal()

    return 0

#text input handler
async def current_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Just send me a link.',reply_markup=ReplyKeyboardRemove())
    if str(update.effective_user.id) in soid:
        await update.message.reply_text('\U0001F618')

#processing the link provided by user, if OK, show keyboard and call process_choice function
#SENDING LINK
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('It looks like a link. Wait until I check it thoroughly, generate downloading links and send them to you.', reply_markup=ReplyKeyboardRemove())
    if str(update.effective_user.id) in soid:
        await update.message.reply_text('Сделаю ссылочки для любимой \U00002764')
    try:
        link = re.search(yt_link_reg_clean, update.message.text).group()
    except AttributeError:
        await update.message.reply_text('Strangely i was unable to extract a link from the text you sent me.', reply_markup=ReplyKeyboardRemove())
        return 0
    
    #Separate thread for function which generate link
    thread = threading.Thread(target=generate_url, args= (context,link,update.message.id,))
    threads.append(thread)
    thread.start()

    context.job_queue.run_repeating(callback=check_status, interval=1, user_id=context._user_id)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="status_cache")
    application = Application.builder().token(TOKEN).persistence(persistence).build()
    
    #W84_CHOICE
    # application.add_handler(
    #     MessageHandler(
    #         filters.Regex("^(Download|Cancel)$"), process_choice
    #     )  
    # )
    #SENDING LINK
    application.add_handler(
        MessageHandler(
            filters.Regex(yt_link_reg), process_link
        )
    )
    application.add_handler(
        MessageHandler(
        filters.TEXT & ~(filters.COMMAND | filters.Regex("^(Download|Cancel)$") | filters.Regex(yt_link_reg)), current_status
        )
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)
    cancel_handler = CommandHandler("cancel", cancel)
    application.add_handler(cancel_handler)
    help_handler = CommandHandler("help", help)
    application.add_handler(help_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
