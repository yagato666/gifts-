from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import GIFTS

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔗 Моя реферальная ссылка", callback_data="ref")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="📦 Мои выводы", callback_data="withdraws")],
    ])

def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu")]
    ])

def subscribe_kb(channels: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = f"https://t.me/{ch.lstrip('@')}"
        rows.append([InlineKeyboardButton(text=f"➕ {ch}", url=url)])
    rows.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def shop_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, v in GIFTS.items():
        rows.append([InlineKeyboardButton(
            text=f"{v['name']} — {v['price']} койнов",
            callback_data=f"buy:{key}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_withdraw_kb(withdraw_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выведено", callback_data=f"adm:approve:{withdraw_id}"),
            InlineKeyboardButton(text="❌ Отказано", callback_data=f"adm:decline:{withdraw_id}"),
        ]
    ])
