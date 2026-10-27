import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

WATCHLIST = {
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF":  "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
}

def get_token_data(address: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("pairs"):
            pair = max(data["pairs"], key=lambda p: p.get("liquidity", {}).get("usd", 0) or 0)
            return {
                "name": pair["baseToken"]["name"],
                "symbol": pair["baseToken"]["symbol"],
                "price": float(pair.get("priceUsd") or 0),
                "volume_24h": pair.get("volume", {}).get("h24", 0),
                "liquidity": pair.get("liquidity", {}).get("usd", 0),
                "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
                "url": pair.get("url", ""),
                "dex": pair.get("dexId", ""),
            }
    except Exception as e:
        print(f"Error fetching {address}: {e}")
    return None

def format_message(data: dict) -> str:
    change = data["price_change_24h"]
    emoji = "🟢" if change >= 0 else "🔴"
    return (
        f"*{data['name']} ({data['symbol']})*\n"
        f"Price: `${data['price']:.8f}`\n"
        f"24h Change: {emoji} `{change:.2f}%`\n"
        f"24h Volume: `${data['volume_24h']:,.0f}`\n"
        f"Liquidity: `${data['liquidity']:,.0f}`\n"
        f"DEX: `{data['dex']}`\n"
        f"[Chart]({data['url']})"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Memecoin Tracker Bot is online!\n\n"
        "Commands:\n"
        "/price <address> - Check any token\n"
        "/watchlist - Show your tracked tokens\n"
        "/check - Check all tokens now"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price <token_address>")
        return
    data = get_token_data(context.args[0])
    if data:
        await update.message.reply_text(format_message(data), parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("Token not found or error.")

async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WATCHLIST:
        await update.message.reply_text("Watchlist is empty.")
        return
    msg = "*Your Watchlist:*\n\n"
    for ticker, address in WATCHLIST.items():
        msg += f"• `{ticker}` → `{address[:10]}...`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Checking all tokens...")
    for ticker, address in WATCHLIST.items():
        data = get_token_data(address)
        if data:
            await update.message.reply_text(format_message(data), parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(1)

def main():
    # Fix for newer Python versions used by Render
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(CommandHandler("check", check))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
