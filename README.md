Telegram bot for youtube video downloading
Click or type /start
Then send any text containing link to youtube video, be it shorts, live or just a regular video.
Bot processes each message independantly and answers with a bunch of links which allow to download 144p 360p 720p or audio only in different formats. To download you have to follow the link in browser. Downloading avaliable from either context, kebab or more options menu. Default video file name is videoplayback.mp4, so rename it by yourself.
The HTTP 403 Forbidden error arises if author of video restricted embedding. There's nothing we can do about it.

Requires 
    environmental variables:
        TOKEN   telegram bot token
        SOID    telegram user id's separated with commas. These users will receive additional messages. 

Uses
    python-telegram-bot
    python-telegram-bot[job-queue]
    pytube

Runs
    docker run -d --rm -e TOKEN="1234567890:TelegramToken" -e SOID=123123123 --name tyd cdoroff/tyd:1.27