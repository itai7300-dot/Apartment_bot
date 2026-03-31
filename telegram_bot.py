import os
import httpx
import asyncio
from anthropic import Anthropic

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

SYSTEM_PROMPT = """אתה חבר טוב שמתמחה בניהול דירות בישראל. המשתמש קנה דירה לאחרונה ואתה עוזר לו בשלושה נושאים:
1. תחזוקה ותיקונים
2. ניהול הוצאות ותקציב
3. שוכרים וחוזים
הסגנון שלך: חברותי, חמים ונינוח. דבר בעברית בלבד."""

client = Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}

async def send_message(chat_id, text):
    async with httpx.AsyncClient() as http:
        await http.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

async def send_typing(chat_id):
    async with httpx.AsyncClient() as http:
        await http.post(f"{BASE_URL}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})

async def handle_update(update):
    msg = update.get("message")
    if not msg or "text" not in msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg["text"]

    if text == "/start" or text == "/reset":
        conversation_history[chat_id] = []
        await send_message(chat_id,
            "🏠 היי! אני הסוכן האישי שלך לניהול הדירה החדשה!\n\n"
            "אני כאן לעזור לך עם:\n"
            "🔧 תחזוקה ותיקונים\n"
            "💰 ניהול הוצאות ותקציב\n"
            "📋 שוכרים וחוזים\n\n"
            "פשוט שאל אותי כל שאלה! 😊"
        )
        return

    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    conversation_history[chat_id].append({"role": "user", "content": text})
    history = conversation_history[chat_id][-20:]

    await send_typing(chat_id)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
        conversation_history[chat_id].append({"role": "assistant", "content": reply})
        await send_message(chat_id, reply)
    except Exception as e:
        await send_message(chat_id, "😅 אופס, משהו השתבש. נסה שוב!")
        print(f"Error: {e}")

async def main():
    print("🤖 הבוט פועל...")
    offset = 0
    async with httpx.AsyncClient(timeout=60) as http:
        while True:
            try:
                r = await http.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30})
                updates = r.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    await handle_update(update)
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
