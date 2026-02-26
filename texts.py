def profile_text(username, user_id, balance, referrals_count):
    u = f"@{username}" if username else "—"
    return (
        "👤 Профиль\n\n"
        f"• Username: {u}\n"
        f"• ID: {user_id}\n"
        f"• Баланс: {balance} 🪙\n"
        f"• Рефералы: {referrals_count}\n"
    )

def need_subscribe_text(channels):
    chs = "\n".join([f"• {c}" for c in channels])
    return (
        "Чтобы пользоваться ботом, подпишись на каналы:\n\n"
        f"{chs}\n\n"
        "После подписки нажми кнопку ниже."
    )

def withdraw_status_text(wid, gift, status):
    return (
        f"🎁 Заявка #{wid}\n\n"
        f"Подарок: {gift}\n"
        f"Статус: {status}"
    )

def status_ru(status: str) -> str:
    statuses = {
        "pending": "⏳ В ожидании",
        "approved": "✅ Выведено",
        "declined": "❌ Отказано",
        "rejected": "❌ Отказано",
        "paid": "💸 Выплачено"
    }
    return statuses.get(status, status)