import enum

from botmanlib.messages import send_or_edit

from src.models import Session, User, Products
from botmanlib.menus.basemenu import BaseMenu
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from botmanlib.menus.helpers import unknown_command, to_state, prepare_user, require_permission
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler


class StartMenu(BaseMenu):
    menu_name = "start_menu"

    class States(enum.Enum):
        ACTION = 1

    def start(self, update, context):
        user = prepare_user(User, update, context)

        self.send_message(context)
        return StartMenu.States.ACTION

    def send_message(self, context):
        user = context.user_data['user']

        buttons = [[InlineKeyboardButton("Просмотр продуктов", callback_data="show_products")]]

        send_or_edit(context,
                     chat_id=user.chat_id,
                     text="Здравствуйте, Вас приветствует бот Products_bot",
                     reply_markup=InlineKeyboardMarkup(buttons))

    @require_permission("access_to_products_for_user")
    def product_for_user(self, update, context):
        telegram_user = update.effective_user
        buttons = [[InlineKeyboardButton("Купить", callback_data="admin_delete")]]
        select_product = Session.query(Products).all()
        message_text = ""
        for product in select_product:
            message_text += ' {}  {}  {}\n'.format(product.id, product.name, product.discription)

        send_or_edit(context,
                     chat_id=telegram_user.id,
                     text="Выберите действие: \n" + message_text,
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
            fallbacks=[MessageHandler(Filters.all, unknown_command(-1))], allow_reentry=True)
        return handler
