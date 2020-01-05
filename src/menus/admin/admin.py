import enum
from src.models import Products, Session, User
from botmanlib.menus.basemenu import BaseMenu
from src.settings import SUPERUSER_ACCOUNTS
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from botmanlib.menus.helpers import unknown_command, add_to_db, to_state
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters


class AdminMenu(BaseMenu):
    menu_name = 'admin_menu'

    class States(enum.Enum):
        ACTION = 1
        END = 2

    def admin_menu(self, update, context):
        if update.message.from_user.id == SUPERUSER_ACCOUNTS:
            buttons = [[InlineKeyboardButton("Продукты", callback_data="admin_products"),
                        InlineKeyboardButton("Рассылка", callback_data="distribution")]]
            update.message.reply_text('Вход админа',
                                      reply_markup=InlineKeyboardMarkup(buttons))
            return self.States.ACTION
        else:
            context.bot.send_message(chat_id=update.message.from_user.id,
                                     text="Ошибка входа")
            return self.States.END

    def product_for_admin(self, update, context):
        telegram_user = update.effective_user
        select_product = Session.query(Products).all()
        query = update.callback_query
        buttons = [[InlineKeyboardButton("Удалить", callback_data="admin_delete"),
                    InlineKeyboardButton("Добавить", callback_data="admin_add"),
                    InlineKeyboardButton("Изменить", callback_data="admin_change")]]
        for product in select_product:
            context.bot.send_message(chat_id=telegram_user.id,
                                     text=' {} '.format(product.id) + ' {} '.format(
                                         product.name) + ' {} '.format(product.discription),
                                     message_id=query.message.message_id)
        context.bot.send_message(chat_id=telegram_user.id, text="Выберите действие: ",
                                 reply_markup=InlineKeyboardMarkup(buttons))

        return self.States.ACTION

    def delete_product(self, update, context):
        telegram_user = update.effective_user
        products = Session.query(Products).first()
        context.bot.send_message(chat_id=telegram_user.id, text="Введите название продукта, который хотите удалить: ")
        text = update.message.text
        buttons = [[InlineKeyboardButton("Старт", callback_data="admin_start")]]
        if text == products.name:
            Session.delete(products)
            Session.commit()
            context.bot.send_message(chat_id=telegram_user.id, text="Продукт был удален ",
                                     reply_markup=InlineKeyboardMarkup(buttons))
            return self.States.ACTION
        else:
            context.bot.send_message(chat_id=telegram_user.id, text="Такого продукта нет ",
                                     reply_markup=InlineKeyboardMarkup(buttons))
            return self.States.END

    def add_product(self, update, context):
        telegram_user = update.effective_user
        context.bot.send_message(chat_id=telegram_user.id,
                                 text="Введите название продукта, затем его описание, чтоб добавить новый продукт: ")
        text = update.message.text

        if 'name' not in context.user_data:
            val = context.validators.String()
            context.user_data['name'] = val.to_python(text)
        elif 'discription' not in context.user_data:
            val = context.validators.Number()
            context.user_data['discription'] = val.to_python(text)
            new_product = Products(name=context.user_data['name'], discription=context.user_data['discription'])
            Session.add(new_product)
            Session.commit()
            context.bot.send_message(chat_id=telegram_user.id, text="Продукт добавлен: ")
            del context.user_data['name']
            del context.user_data['discription']
            return self.States.ACTION

    def distribution(self, update, context):
        telegram_user = update.effective_user
        for i in User.id:
            context.bot.send_message(chat_id=i, text="Привет всем: ")
        context.bot.send_message(chat_id=telegram_user.id, text="Рассылка завершена: ")

    def get_handler(self):

        handler = ConversationHandler(
            entry_points=[CommandHandler('admin', self.admin_menu, pass_user_data=True)],
            states={
                self.States.ACTION: [
                    CallbackQueryHandler(self.product_for_admin,
                                         pattern='admin_products', pass_user_data=True),
                    CallbackQueryHandler(self.delete_product,
                                         pattern='admin_delete', pass_user_data=True),
                    CallbackQueryHandler(self.add_product,
                                         pattern='admin_add', pass_user_data=True),
                    CallbackQueryHandler(self.distribution,
                                         pattern='distribution', pass_user_data=True),

                    MessageHandler(Filters.all, to_state(self.States.ACTION))],
                self.States.END: [CallbackQueryHandler(self.admin_menu, pass_user_data=True),
                                  MessageHandler(Filters.all, to_state(self.States.END))]
            },
            fallbacks=[MessageHandler(Filters.all, unknown_command(-1), pass_user_data=True)], allow_reentry=True)
        return handler
