import asyncio
import logging
import httpx
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())


def headers_for(user_id: int) -> dict:
    return {
        "X-API-Key": settings.internal_api_key,
        "X-TG-UserId": str(user_id),
    }


def key_only() -> dict:
    return {
        "X-API-Key": settings.internal_api_key,
    }


class AddUsed(StatesGroup):
    title = State()
    imei = State()
    grade = State()
    battery = State()
    sell_price = State()
    purchase_price = State()
    notes = State()


_last_notified_lead_id = 0


def lead_kb(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Взять", callback_data=f"lead_take:{lead_id}"),
                InlineKeyboardButton(text="🟦 Закрыть", callback_data=f"lead_close:{lead_id}"),
            ]
        ]
    )


def parse_phone_post(text: str) -> dict:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    title = lines[0] if lines else "Без названия"

    grade_match = re.search(r"(?:Состояние|Grade)\s*:\s*([ABCabc])", text)
    battery_match = re.search(r"(?:Battery|Батарея)\s*:\s*(\d{1,3})", text)
    price_match = re.search(r"(?:Цена|Price)\s*:\s*([\d\s]+)", text)
    imei_match = re.search(r"IMEI\s*:\s*([0-9A-Za-z\-]+)", text)

    return {
        "title": title,
        "condition_grade": grade_match.group(1).upper() if grade_match else "B",
        "battery_health": int(battery_match.group(1)) if battery_match else None,
        "sell_price_uzs": int(price_match.group(1).replace(" ", "")) if price_match else 0,
        "purchase_price_uzs": None,
        "imei": imei_match.group(1) if imei_match else None,
        "notes": text,
    }


async def process_forwarded_post(message: Message, caption: str):
    data = parse_phone_post(caption)

    if not data["imei"]:
        await message.reply("Не найден IMEI в сообщении. Используй формат: IMEI: 123456")
        return

    if not data["sell_price_uzs"]:
        await message.reply("Не найдена цена. Используй формат: Цена: 12000000")
        return

    photo_file_id = message.photo[-1].file_id if message.photo else None

    payload = {
        "title": data["title"],
        "condition_grade": data["condition_grade"],
        "battery_health": data["battery_health"],
        "imei": data["imei"],
        "sell_price_uzs": data["sell_price_uzs"],
        "purchase_price_uzs": data["purchase_price_uzs"],
        "notes": data["notes"] + (f"\n\nPHOTO_FILE_ID: {photo_file_id}" if photo_file_id else ""),
        "telegram_photo_file_id": photo_file_id,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{settings.core_url}/inventory/bot/used",
            json=payload,
            headers=headers_for(message.from_user.id),
        )

    if r.status_code != 200:
        await message.reply(f"Не удалось добавить товар: {r.status_code}\n{r.text}")
        return

    item = r.json()
    await message.reply(
        f"✅ Товар добавлен из пересланного поста\n"
        f"#{item['id']} {item['title']} | {item['sell_price_uzs']} UZS"
    )


async def poll_leads_task():
    global _last_notified_lead_id
    await asyncio.sleep(2)

    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{settings.core_url}/leads/pending",
                    headers=key_only(),
                )

            if r.status_code == 200:
                leads = r.json()
                leads_sorted = sorted(leads, key=lambda x: x["id"])

                for lead in leads_sorted:
                    if lead["id"] <= _last_notified_lead_id:
                        continue

                    msg = (
                        "🟨 Новая заявка на рассрочку\n"
                        f"ID: {lead['id']}\n"
                        f"Товар: #{lead['item_id']} — {lead['item_title']}\n"
                        f"ФИО: {lead['full_name']}\n"
                        f"Тел: {lead['phone']}\n"
                        f"Срок: {lead['installment_months']} мес\n"
                        f"Комментарий: {lead['comment'] or '-'}"
                    )

                    await bot.send_message(
                        settings.manager_chat_id,
                        msg,
                        reply_markup=lead_kb(lead["id"]),
                    )

                    _last_notified_lead_id = lead["id"]

        except Exception as e:
            logging.warning(f"Lead poll error: {e}")

        await asyncio.sleep(8)


@dp.callback_query(F.data.startswith("lead_take:"))
async def lead_take(cb: CallbackQuery):
    lead_id = int(cb.data.split(":", 1)[1])

    payload = {
        "status": "in_progress",
        "assigned_to_telegram_id": cb.from_user.id,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{settings.core_url}/leads/{lead_id}/update",
            json=payload,
            headers=key_only(),
        )

    if r.status_code != 200:
        await cb.answer("Ошибка", show_alert=True)
        await cb.message.answer(f"update lead error {r.status_code}: {r.text}")
        return

    await cb.answer("Взято ✅")
    await cb.message.edit_text(
        cb.message.text + f"\n\n✅ Взял: {cb.from_user.full_name}",
        reply_markup=None,
    )


@dp.callback_query(F.data.startswith("lead_close:"))
async def lead_close(cb: CallbackQuery):
    lead_id = int(cb.data.split(":", 1)[1])

    payload = {
        "status": "closed",
        "assigned_to_telegram_id": cb.from_user.id,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{settings.core_url}/leads/{lead_id}/update",
            json=payload,
            headers=key_only(),
        )

    if r.status_code != 200:
        await cb.answer("Ошибка", show_alert=True)
        await cb.message.answer(f"update lead error {r.status_code}: {r.text}")
        return

    await cb.answer("Закрыто 🟦")
    await cb.message.edit_text(
        cb.message.text + f"\n\n🟦 Закрыл: {cb.from_user.full_name}",
        reply_markup=None,
    )


@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "Панель команд:\n"
        "➕ Добавить Б/У: /add_used\n"
        "📦 Склад поиск: /stock iphone 13   или   /stock IMEI:123\n"
        "✅ Продажа: /sell IMEI:123 price:15000000 pay:uzum_nasiya channel:shop\n"
        "📊 Сегодня: /today\n"
        "📈 Средние: /avg\n"
        "🔮 Прогноз: /forecast 30\n"
        "🧾 Лиды: приходят автоматом в чат менеджеров\n"
        "📨 Можно переслать пост из канала с фото и подписью телефона"
    )


@dp.message(F.text == "/today")
async def today(message: Message):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{settings.core_url}/reports/today",
            headers=key_only(),
        )
    await message.answer(f"HTTP {r.status_code}\n{r.text}")


@dp.message(F.text == "/avg")
async def avg(message: Message):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{settings.core_url}/reports/averages",
            headers=key_only(),
        )

    if r.status_code != 200:
        await message.answer(f"Ошибка {r.status_code}: {r.text}")
        return

    rows = r.json()
    lines = ["📈 Средние продажи:"]
    for row in rows:
        lines.append(
            f"{row['days']}д: {row['avg_sales_per_day']} продаж/день, "
            f"{int(row['avg_revenue_uzs_per_day'])} UZS/день | "
            f"итого {row['total_sales']} продаж, {row['total_revenue_uzs']} UZS"
        )

    await message.answer("\n".join(lines))


@dp.message(F.text.startswith("/forecast"))
async def forecast(message: Message):
    parts = message.text.split()
    basis = 30

    if len(parts) > 1:
        try:
            basis = int(parts[1])
        except Exception:
            basis = 30

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{settings.core_url}/reports/forecast/30d",
            params={"basis_days": basis},
            headers=key_only(),
        )

    if r.status_code != 200:
        await message.answer(f"Ошибка {r.status_code}: {r.text}")
        return

    d = r.json()
    await message.answer(
        "🔮 Прогноз на 30 дней\n"
        f"Основа: {d['basis_days']} дней\n"
        f"Среднее: {d['avg_sales_per_day']} продаж/день, {int(d['avg_revenue_uzs_per_day'])} UZS/день\n"
        f"Ожидание: {d['expected_sales_30d']} продаж, {int(d['expected_revenue_uzs_30d'])} UZS"
    )


@dp.message(F.text.startswith("/stock"))
async def stock(message: Message):
    q = message.text.replace("/stock", "").strip()

    if not q:
        await message.answer("Формат: /stock iphone 13   или   /stock IMEI:123")
        return

    params = {}
    if q.lower().startswith("imei:"):
        params["imei"] = q.split(":", 1)[1].strip()
    else:
        params["q"] = q

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{settings.core_url}/inventory/bot/search",
            params=params,
            headers=headers_for(message.from_user.id),
        )

    if r.status_code != 200:
        await message.answer(f"Ошибка {r.status_code}: {r.text}")
        return

    items = r.json()
    if not items:
        await message.answer("Ничего не найдено.")
        return

    lines = []
    for it in items[:15]:
        lines.append(
            f"#{it['id']} | {it['title']} | {it['status']} | {it['sell_price_uzs']} UZS | IMEI {it.get('imei')}"
        )

    await message.answer("\n".join(lines))


@dp.message(F.text.startswith("/sell"))
async def sell(message: Message):
    text = message.text.replace("/sell", "").strip()

    if not text:
        await message.answer(
            "Формат: /sell IMEI:123 price:15000000 pay:cash|uzum_nasiya channel:shop|online"
        )
        return

    parts = text.split()
    data = {
        "channel": "shop",
        "payment_type": "cash",
    }

    for p in parts:
        pl = p.lower()
        if pl.startswith("imei:"):
            data["imei"] = p.split(":", 1)[1].strip()
        elif pl.startswith("price:"):
            data["sell_price_uzs"] = int(p.split(":", 1)[1].strip())
        elif pl.startswith("pay:"):
            data["payment_type"] = p.split(":", 1)[1].strip()
        elif pl.startswith("channel:"):
            data["channel"] = p.split(":", 1)[1].strip()

    if "imei" not in data or "sell_price_uzs" not in data:
        await message.answer(
            "Нужно IMEI и price. Пример: /sell IMEI:123 price:15000000 pay:uzum_nasiya channel:shop"
        )
        return

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{settings.core_url}/inventory/bot/sell",
            json=data,
            headers=headers_for(message.from_user.id),
        )

    if r.status_code != 200:
        await message.answer(f"Не продалось: {r.status_code}\n{r.text}")
        return

    await message.answer(
        f"✅ Продано: IMEI {data['imei']} за {data['sell_price_uzs']} UZS ({data['payment_type']}, {data['channel']})"
    )


@dp.message(F.text == "/add_used")
async def add_used_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddUsed.title)
    await message.answer("Название (пример: iPhone 13 128 Blue):")


@dp.message(AddUsed.title)
async def add_used_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddUsed.imei)
    await message.answer("IMEI (уникальный):")


@dp.message(AddUsed.imei)
async def add_used_imei(message: Message, state: FSMContext):
    await state.update_data(imei=message.text.strip())
    await state.set_state(AddUsed.grade)
    await message.answer("Grade (A/B/C):")


@dp.message(AddUsed.grade)
async def add_used_grade(message: Message, state: FSMContext):
    g = message.text.strip().upper()
    if g not in ("A", "B", "C"):
        await message.answer("Только A, B или C.")
        return

    await state.update_data(condition_grade=g)
    await state.set_state(AddUsed.battery)
    await message.answer("Battery % (0-100) или 0 если неизвестно:")


@dp.message(AddUsed.battery)
async def add_used_battery(message: Message, state: FSMContext):
    try:
        bh = int(message.text.strip())
        if bh < 0 or bh > 100:
            raise ValueError()
    except Exception:
        await message.answer("Введи число 0..100.")
        return

    await state.update_data(battery_health=None if bh == 0 else bh)
    await state.set_state(AddUsed.sell_price)
    await message.answer("Цена продажи UZS (число):")


@dp.message(AddUsed.sell_price)
async def add_used_sell_price(message: Message, state: FSMContext):
    try:
        sp = int(message.text.strip())
        if sp < 0:
            raise ValueError()
    except Exception:
        await message.answer("Введи целое число >= 0.")
        return

    await state.update_data(sell_price_uzs=sp)
    await state.set_state(AddUsed.purchase_price)
    await message.answer("Цена закупа UZS (число) или 0 если нет:")


@dp.message(AddUsed.purchase_price)
async def add_used_purchase_price(message: Message, state: FSMContext):
    try:
        pp = int(message.text.strip())
        if pp < 0:
            raise ValueError()
    except Exception:
        await message.answer("Введи целое число >= 0.")
        return

    await state.update_data(purchase_price_uzs=None if pp == 0 else pp)
    await state.set_state(AddUsed.notes)
    await message.answer("Заметки (или '-' если нет):")


@dp.message(AddUsed.notes)
async def add_used_notes(message: Message, state: FSMContext):
    data = await state.get_data()
    notes = message.text.strip()
    if notes == "-":
        notes = ""

    payload = {
        "title": data["title"],
        "condition_grade": data["condition_grade"],
        "battery_health": data["battery_health"],
        "imei": data["imei"],
        "sell_price_uzs": data["sell_price_uzs"],
        "purchase_price_uzs": data["purchase_price_uzs"],
        "notes": notes,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{settings.core_url}/inventory/bot/used",
            json=payload,
            headers=headers_for(message.from_user.id),
        )

    if r.status_code != 200:
        await message.answer(f"Не сохранилось: {r.status_code}\n{r.text}")
    else:
        it = r.json()
        await message.answer(
            f"✅ Добавлено: #{it['id']} {it['title']} | {it['sell_price_uzs']} UZS | IMEI {it.get('imei')}"
        )

    await state.clear()


@dp.message(F.photo)
async def handle_photo_post(message: Message):
    # Ловим:
    # 1) пересланные посты из канала
    # 2) просто фото + подпись
    # 3) просто загруженные фото с текстом

    caption = message.caption or message.text or ""
    if not caption.strip():
        await message.reply(
            "Нужно фото и подпись.\n\n"
            "Пример:\n"
            "iPhone 13 128 Blue\n"
            "Состояние: A\n"
            "Battery: 92\n"
            "Цена: 11800000\n"
            "IMEI: 123456789"
        )
        return

    try:
        await process_forwarded_post(message, caption)
    except Exception as e:
        await message.reply(f"Ошибка обработки: {e}")


async def main():
    logging.info("Bot started polling...")
    asyncio.create_task(poll_leads_task())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())