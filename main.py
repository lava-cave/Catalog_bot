from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
import os

ADMIN_ID = 7182594067

with open("data/catalog.json", "r", encoding="utf-8") as f:
    furniture_catalog = json.load(f)

ADD_CATEGORY, ADD_NAME, ADD_PRICE, ADD_DESCRIPTION, ADD_IMAGE = range(5)
admin_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(category, callback_data=category)] for category in furniture_catalog]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию мебели:", reply_markup=reply_markup)

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    items = furniture_catalog.get(category, [])
    for item in items:
        text = f"*{item['name']}*\nЦена: {item['price']}\n{item['description']}"
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=item['image'], caption=text, parse_mode='Markdown')

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return ConversationHandler.END
    await update.message.reply_text("Введите категорию:")
    return ADD_CATEGORY

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_temp[update.effective_user.id] = {"category": update.message.text}
    await update.message.reply_text("Введите название товара:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_temp[update.effective_user.id]["name"] = update.message.text
    await update.message.reply_text("Введите цену товара:")
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_temp[update.effective_user.id]["price"] = update.message.text
    await update.message.reply_text("Введите описание товара:")
    return ADD_DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_temp[update.effective_user.id]["description"] = update.message.text
    await update.message.reply_text("Введите ссылку на изображение товара:")
    return ADD_IMAGE

async def add_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = admin_temp[update.effective_user.id]
    user_data["image"] = update.message.text

    product = {
        "name": user_data["name"],
        "price": user_data["price"],
        "description": user_data["description"],
        "image": user_data["image"]
    }

    category = user_data["category"]
    if category not in furniture_catalog:
        furniture_catalog[category] = []
    furniture_catalog[category].append(product)

    with open("data/catalog.json", "w", encoding="utf-8") as f:
        json.dump(furniture_catalog, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Товар добавлен в категорию '{category}'")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Добавление отменено.")
    return ConversationHandler.END

app = ApplicationBuilder().token("8047969302:AAEIlPBz9rtx3n1XV1KTY2Dz061Dq9nHIrw").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(category_selected))

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add_start)],
    states={
        ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
        ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
        ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
        ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
        ADD_IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_image)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)
app.run_polling()
