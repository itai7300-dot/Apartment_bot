import os
from anthropic import Anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ─── הגדרות ───────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SYSTEM_PROMPT = """אתה חבר טוב שמתמחה בניהול דירות בישראל. המשתמש קנה דירה לאחרונה ואתה עוזר לו בשלושה נושאים:

1. תחזוקה ותיקונים – תחזוקה שוטפת, זיהוי בעיות, המלצות על בעלי מקצוע, תיעדוף תיקונים.
2. ניהול הוצאות ותקציב – מעקב הוצאות, תכנון תקציב שנתי, ועד בית, ארנונה, ביטוח.
3. שוכרים וחוזים – ייעוץ בהשכרה, ניסוח חוזים, זכויות וחובות, פתרון סכסוכים.

הסגנון שלך: חברותי, חמים ונינוח — כמו שיחה עם חבר שמבין בנושא. השתמש בשפה יומיומית ואמוג'י במידה. דבר בעברית בלבד."""

# שמירת היסטוריית שיחה לכל משתמש
conversation_history: dict[int, list] = {}
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── פקודת /start ─────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "🏠 היי! אני הסוכן האישי שלך לניהול הדירה החדשה!\n\n"
        "אני כאן לעזור לך עם:\n"
        "🔧 תחזוקה ותיקונים\n"
        "💰 ניהול הוצאות ותקציב\n"
        "📋 שוכרים וחוזים\n\n"
        "פשוט שאל אותי כל שאלה! 😊\n\n"
        "טיפ: /reset מאפס את השיחה"
    )

# ─── פקודת /reset ─────────────────────────────────────────
async def reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ השיחה אופסה! בוא נתחיל מחדש 🏠")

# ─── טיפול בהודעות ────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # הוספת הודעת המשתמש להיסטוריה
    conversation_history[user_id].append({"role": "user", "content": user_text})

    # שמירה על מקסימום 20 הודעות אחרונות (לחסוך tokens)
    history = conversation_history[user_id][-20:]

    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text

        # שמירת תגובת הבוט להיסטוריה
        conversation_history[user_id].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("😅 אופס, משהו השתבש. נסה שוב!")
        print(f"Error: {e}")

# ─── הפעלת הבוט ───────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 הבוט פועל...")
    app.run_polling()
