import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from config import load_config, GIFTS
import db
import keyboards as kb
import texts

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()

BOT_USERNAME: Optional[str] = None  


def parse_referrer(args: Optional[str], self_user_id: int) -> Optional[int]:
    """
    /start <referrer_id>
    """
    if not args:
        return None
    args = args.strip()
    if not args.isdigit():
        return None
    rid = int(args)
    if rid == self_user_id:
        return None
    return rid


async def is_subscribed(bot: Bot, user_id: int, channels: list[str]) -> bool:
    for ch in channels:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ("member", "administrator", "creator"):
                return False
        except TelegramBadRequest:
            return False
        except Exception:
            return False
    return True


async def ensure_verified_and_reward(bot: Bot, user_id: int, cfg) -> bool:
    """
    If user subscribed => mark verified.
    If this is the first time user becomes verified AND has referrer_id AND not rewarded => +1 coin to referrer.
    """
    user = await db.get_user(user_id)
    if not user:
        return False

    ok = await is_subscribed(bot, user_id, cfg.channels)
    if not ok:
        return False

    if user["verified"] == 0:
        await db.set_verified(user_id, True)

    if user["referrer_id"] and user["referral_rewarded"] == 0:
        ref_id = int(user["referrer_id"])
        ref_user = await db.get_user(ref_id)
        if ref_user:
            await db.add_balance(ref_id, 1)
            await db.inc_referrals_count(ref_id, 1)
        else:
            await db.upsert_user(ref_id, None, None)
            await db.add_balance(ref_id, 1)
            await db.inc_referrals_count(ref_id, 1)

        await db.mark_referral_rewarded(user_id)

    return True


async def send_menu(message_or_call, text: str):
    if isinstance(message_or_call, Message):
        await message_or_call.answer(text, reply_markup=kb.main_menu(), parse_mode="Markdown")
    else:
        await message_or_call.message.edit_text(text, reply_markup=kb.main_menu(), parse_mode="Markdown")


@dp.message(CommandStart())
async def start(message: Message, command: CommandStart, bot: Bot):
    cfg = load_config()
    user_id = message.from_user.id
    username = message.from_user.username

    args = message.text.split(maxsplit=1)
    ref_args = args[1] if len(args) > 1 else None
    referrer_id = parse_referrer(ref_args, user_id)

    await db.upsert_user(user_id, username, referrer_id)

    ok = await ensure_verified_and_reward(bot, user_id, cfg)
    if not ok:
        await message.answer(
            texts.need_subscribe_text(cfg.channels),
            reply_markup=kb.subscribe_kb(cfg.channels),
            parse_mode="Markdown",
        )
        return

    user = await db.get_user(user_id)
    text = texts.profile_text(username, user_id, user["balance"], user["referrals_count"])
    await send_menu(message, text)


@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, bot: Bot):
    cfg = load_config()
    user_id = call.from_user.id

    ok = await ensure_verified_and_reward(bot, user_id, cfg)
    if not ok:
        await call.answer("Подписка не найдена. Подпишись на все каналы и попробуй ещё раз.", show_alert=True)
        return

    user = await db.get_user(user_id)
    text = texts.profile_text(call.from_user.username, user_id, user["balance"], user["referrals_count"])
    await call.message.edit_text(text, reply_markup=kb.main_menu(), parse_mode="Markdown")


@dp.callback_query(F.data == "menu")
async def menu(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    if not user:
        await call.answer("Напиши /start", show_alert=True)
        return

    text = texts.profile_text(call.from_user.username, call.from_user.id, user["balance"], user["referrals_count"])
    await call.message.edit_text(text, reply_markup=kb.main_menu(), parse_mode="Markdown")


@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    if not user:
        await call.answer("Напиши /start", show_alert=True)
        return
    text = texts.profile_text(call.from_user.username, call.from_user.id, user["balance"], user["referrals_count"])
    await call.message.edit_text(text, reply_markup=kb.main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "ref")
async def ref_link(call: CallbackQuery):
    global BOT_USERNAME
    if not BOT_USERNAME:
        await call.answer("Бот ещё не готов. Попробуй позже.", show_alert=True)
        return

    user_id = call.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    text = (
        "🔗 Твоя реферальная ссылка\n\n"
        f"{link}\n\n"
        "Пригласи друга: когда он запустит бота и подпишется на каналы — ты получишь 1 🪙."
    )

    await call.message.edit_text(
        text,
        reply_markup=kb.back_to_menu()
    )

@dp.callback_query(F.data == "shop")
async def shop(call: CallbackQuery):
    text = "🛒 *Магазин*\n\nВыбери подарок для обмена:"
    await call.message.edit_text(text, reply_markup=kb.shop_kb(), parse_mode="Markdown")

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    cfg = load_config()

    if message.from_user.id not in cfg.admins:
        await message.answer("Нет доступа.")
        return

    s = await db.admin_stats()
    text = (
        "📊 Статистика бота\n\n"
        f"👥 Пользователей: {s['users']}\n"
        f"🟢 Подписанных: {s['verified']}\n\n"
        f"🪙 Всего койнов выдано: {s['coins']}\n"
        f"📤 Всего заявок: {s['withdraws']}\n\n"
        f"⏳ В ожидании: {s['pending']}\n"
        f"✅ Выведено: {s['approved']}\n"
        f"❌ Отказано: {s['declined']}"
    )

    await message.answer(text)
    
@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery, bot: Bot):
    cfg = load_config()
    user_id = call.from_user.id
    key = call.data.split(":", 1)[1]

    if key not in GIFTS:
        await call.answer("Товар не найден.", show_alert=True)
        return

    user = await db.get_user(user_id)
    if not user:
        await call.answer("Напиши /start", show_alert=True)
        return

    gift = GIFTS[key]
    cost = gift["price"]
    if user["balance"] < cost:
        await call.answer("Недостаточно койнов 😕", show_alert=True)
        return


    await db.subtract_balance(user_id, cost)
    wid = await db.create_withdraw(user_id, key, gift["name"], cost)


    u = f"@{call.from_user.username}" if call.from_user.username else "—"
    admin_text = (
        "📤 *Новый вывод*\n\n"
        f"👤 {u}\n"
        f"🆔 `{user_id}`\n"
        f"🎁 Подарок: *{gift['name']}*\n"
        f"💸 Списано: *{cost}* 🪙\n"
        f"🧾 Заявка: *#{wid}*"
    )
    await bot.send_message(
        chat_id=cfg.admins_chat_id,
        text=admin_text,
        reply_markup=kb.admin_withdraw_kb(wid),
        parse_mode="Markdown",
    )

    await call.answer("Заявка на вывод создана ✅", show_alert=True)
    await call.message.edit_text("✅ Заявка создана! Статус смотри в разделе *Мои выводы*.", reply_markup=kb.back_to_menu(), parse_mode="Markdown")


@dp.callback_query(F.data == "withdraws")
async def my_withdraws(call: CallbackQuery):
    user_id = call.from_user.id
    items = await db.get_user_withdraws(user_id, limit=20)
    if not items:
        await call.message.edit_text("📦 *Мои выводы*\n\nПока нет заявок.", reply_markup=kb.back_to_menu(), parse_mode="Markdown")
        return

    lines = ["📦 *Мои выводы*\n"]
    for w in items:
        lines.append(
            f"• `#{w['id']}` {w['gift_name']} — {texts.status_ru(w['status'])}"
        )
    await call.message.edit_text("\n".join(lines), reply_markup=kb.back_to_menu(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("adm:"))
async def admin_action(call: CallbackQuery, bot: Bot):
    cfg = load_config()
    if call.message.chat.id != cfg.admins_chat_id:
        await call.answer("Недоступно.", show_alert=True)
        return

    _, action, wid_raw = call.data.split(":")
    wid = int(wid_raw)

    w = await db.get_withdraw(wid)
    if not w:
        await call.answer("Заявка не найдена.", show_alert=True)
        return

    if w["status"] != "pending":
        await call.answer("Уже обработано.", show_alert=True)
        return

    if action == "approve":
        await db.set_withdraw_status(wid, "approved")

        await bot.send_message(
            w["user_id"],
            texts.withdraw_status_text(wid, w["gift_name"], "✅ Выведено")
        )

        await call.message.edit_text(call.message.text + "\n\n✅ Статус: Выведено")
        await call.answer("Готово")

    elif action == "decline":
        await db.set_withdraw_status(wid, "declined")

        await bot.send_message(
            w["user_id"],
            texts.withdraw_status_text(wid, w["gift_name"], "❌ Отказано")
        )

        await call.message.edit_text(call.message.text + "\n\n❌ Статус: Отказано")
        await call.answer("Готово")



async def main():
    global BOT_USERNAME
    cfg = load_config()
    await db.init_db()

    bot = Bot(cfg.bot_token)
    me = await bot.get_me()
    BOT_USERNAME = me.username

    logging.info("Bot username: @%s", BOT_USERNAME)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
