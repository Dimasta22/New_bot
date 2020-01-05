import enum

from botmanlib.menus import InstantDistributionMenu
from botmanlib.messages import send_or_edit, delete_interface, remove_interface_markup
from formencode import validators
from sqlalchemy import func

from src.models import Products, Session, User
from botmanlib.menus.basemenu import BaseMenu
from src.settings import SUPERUSER_ACCOUNTS
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from botmanlib.menus.helpers import unknown_command, add_to_db, to_state, prepare_user
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, PrefixHandler


class AdminMenu(BaseMenu):
    menu_name = 'admin_menu'

    class States(enum.Enum):
        ACTION = 1
        END = 2

    def entry(self, update, context):
        user = prepare_user(User, update, context)

        if self.menu_name not in context.user_data:
            context.user_data[self.menu_name] = {}

        if user.chat_id == SUPERUSER_ACCOUNTS:
            self.send_message(context)
            return self.States.ACTION
        else:
            send_or_edit(context,
                         chat_id=update.message.from_user.id,
                         text="Ошибка входа")
            return self.States.END

    def send_message(self, context):
        user = context.user_data['user']

        buttons = [[InlineKeyboardButton("Продукты", callback_data="admin_products"),
                    InlineKeyboardButton("Рассылка", callback_data="distribution")]]
        send_or_edit(context, chat_id=user.chat_id, text='Вход админа', reply_markup=InlineKeyboardMarkup(buttons))

    def product_for_admin(self, update, context):
        telegram_user = update.effective_user
        select_product = Session.query(Products).all()
        query = update.callback_query
        buttons = [[InlineKeyboardButton("Удалить", callback_data="admin_delete"),
                    InlineKeyboardButton("Добавить", callback_data="admin_add"),
                    InlineKeyboardButton("Изменить", callback_data="admin_change")]]
        for product in select_product:
            send_or_edit(context, chat_id=telegram_user.id,
                         text=' {} '.format(product.id) + ' {} '.format(
                             product.name) + ' {} '.format(product.discription))
        send_or_edit(context, chat_id=telegram_user.id, text="Выберите действие: ",
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
        if update.message:
            text = update.message.text
        else:
            context.bot.send_message(chat_id=telegram_user.id, text="Введите название продукта, затем его описание, чтоб добавить новый продукт: ")
            return self.States.ACTION

        if 'name' not in context.user_data[self.menu_name]:
            val = validators.String()
            context.user_data[self.menu_name]['name'] = val.to_python(text)
            context.bot.send_message(chat_id=telegram_user.id, text="Введите описание продукта:")
        elif 'discription' not in context.user_data[self.menu_name]:
            val = validators.String()
            context.user_data[self.menu_name]['discription'] = val.to_python(text)
            new_product = Products(name=context.user_data[self.menu_name]['name'], discription=context.user_data[self.menu_name]['discription'])
            Session.add(new_product)
            Session.commit()
            delete_interface(context)
            send_or_edit(context, chat_id=telegram_user.id, text="Продукт добавлен: ")
            del context.user_data[self.menu_name]['name']
            del context.user_data[self.menu_name]['discription']
            return self.States.ACTION

    def distribution(self, update, context):
        telegram_user = update.effective_user
        users = Session.query(User).filter(User.is_active == True).all()

        for user in users:
            context.bot.send_message(chat_id=user.chat_id, text="Привет всем: ")

        context.bot.send_message(chat_id=telegram_user.id, text="Рассылка завершена: ")

    def goto_next_menu(self, update, context):
        context.update_queue.put(update)
        return ConversationHandler.END

    def get_handler(self):
        distribution_menu = Distribution(User, self)
        handler = ConversationHandler(
            entry_points=[CommandHandler('admin', self.entry, pass_user_data=True)],
            states={
                self.States.ACTION: [
                    PrefixHandler("/", "start", self.goto_next_menu),
                    CallbackQueryHandler(self.product_for_admin,
                                         pattern='admin_products', pass_user_data=True),
                    CallbackQueryHandler(self.delete_product,
                                         pattern='admin_delete', pass_user_data=True),
                    CallbackQueryHandler(self.add_product, pattern='admin_add', pass_user_data=True),
                    MessageHandler(Filters.text, self.add_product),
                    distribution_menu.handler,

                    MessageHandler(Filters.all, to_state(self.States.ACTION))],
                self.States.END: [CallbackQueryHandler(self.entry, pass_user_data=True),
                                  MessageHandler(Filters.all, to_state(self.States.END))]
            },
            fallbacks=[MessageHandler(Filters.all, unknown_command(-1), pass_user_data=True)], allow_reentry=True)
        return handler


class Distribution(InstantDistributionMenu):
    pass

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^distribution$")]
