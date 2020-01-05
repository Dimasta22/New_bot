import os

from telegram.ext import messagequeue
from telegram.utils.request import Request

from botmanlib.bot import BotmanBot
from botmanlib.updater import BotmanUpdater

from src.menus.user.start import StartMenu
from src.menus.admin.admin import AdminMenu


def main():
    bot_token = os.environ['bot.token']
    mqueue = messagequeue.MessageQueue(all_burst_limit=30, all_time_limit_ms=1000)
    request = Request(con_pool_size=8)

    bot = BotmanBot(token=bot_token, request=request, mqueue=mqueue)
    updater = BotmanUpdater(bot=bot, use_context=True, use_sessions=True)

    dispatcher = updater.dispatcher

    start_menu = StartMenu(bot=bot, dispatcher=dispatcher)
    admin_menu = AdminMenu(bot=bot, dispatcher=dispatcher)
    dispatcher.add_handler(admin_menu.handler)
    dispatcher.add_handler(start_menu.handler)

    updater.start_polling()
    updater.idle()

    bot.stop()


if __name__ == "__main__":
    main()
