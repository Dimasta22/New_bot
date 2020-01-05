import enum
from src.models import Session, User, Products
from botmanlib.menus.basemenu import BaseMenu
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from botmanlib.menus.helpers import unknown_command, to_state
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler


class StartMenu(BaseMenu):
    menu_name = "start_menu"

    class States(enum.Enum):
        ACTION = 1

    def start(self, update, context):
        buttons = [[InlineKeyboardButton("Просмотр продуктов", callback_data="show_products")]]
        context.bot.send_message(chat_id=update.message.from_user.id,
                                 text="Здравствуйте, Вас приветствует бот Products_bot",
                                 reply_markup=InlineKeyboardMarkup(buttons))
        telegram_user = update.message.from_user

        user = Session.query(User).filter(User.chat_id == telegram_user.id).first()
        if user is None:
            Session.add(
                User(
                    chat_id=telegram_user.id,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    username=telegram_user.username
                )
            )
            Session.commit()

        return StartMenu.States.ACTION

    def product_for_user(self, update, context):
        telegram_user = update.effective_user
        buttons = [[InlineKeyboardButton("Купить", callback_data="admin_delete")]]
        select_product = Session.query(Products).all()
        for product in select_product:
            context.bot.send_message(chat_id=telegram_user.id,
                                     ttext=' {} '.format(product.id) + ' {} '.format(
                                         product.name) + ' {} '.format(product.discription))
        context.bot.send_message(chat_id=telegram_user.id, text="Выберите действие: ",
                                 reply_markup=InlineKeyboardMarkup(buttons))
        return self.States.ACTION

    def get_handler(self):

        handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start, pass_user_data=True)],
            states={
                self.States.ACTION: [CallbackQueryHandler(self.product_for_user,
                                                          pattern='show_products', pass_user_data=True),

                                     MessageHandler(Filters.all, to_state(StartMenu.States.ACTION))],
            },
            fallbacks=[MessageHandler(Filters.all, unknown_command(-1), pass_user_data=True)], allow_reentry=True)
        return handler
