import telegram.ext
import telegram
from telegram.ext import CommandHandler
import requests
import json
import time
from tracker import get_prices
import asyncio
from translate import Translator
from bs4 import BeautifulSoup




print('bot is starting...')
time.sleep(2)

# enter below your telegram bot token you find in the "botfather".
bot_token = '5829520085:AAGTk0Kp49fJ1_MA9LQhcs6s4-cRYwfY1KM'
bot = telegram.Bot(token=bot_token)

updater = telegram.ext.Updater(token=bot_token, use_context=True)
print("API loaded correctly...")


latest_news = None
dispatcher = updater.dispatcher


async def get_latest_news():
    global latest_news, latest_news_link
    while True:
        url = 'https://cryptopotato.com/'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_headlines = soup.find_all('div', {'class': 'media-body'})
        if news_headlines:
            current_latest_news = news_headlines[0].get_text().strip()
            current_latest_news_link = news_headlines[0].find('a')['href']
            if current_latest_news != latest_news:
                latest_news = current_latest_news
                latest_news_link = current_latest_news_link
                yield latest_news
            else:
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(60)

async def send_message():
    async for latest_news in get_latest_news():
        translator = Translator(to_lang='pl')
        translation = translator.translate(latest_news)
        message = f"{translation}\n\n{latest_news_link}"
        try:
            last_message = bot.send_message(chat_id='@kryptopolska_pl', text=message, parse_mode='HTML', reply_to_message_id=85775)
        except telegram.error.BadRequest as e:
            # Handle the case when the original message was deleted
            last_message = bot.send_message(chat_id='@kryptopolska_pl', text=message, parse_mode='HTML')
        # Save the message ID so that we can reply to it next time
        message_thread_id = last_message.message_id
        await asyncio.sleep(60)



# function responsible for take by API coin price you want to get to know.
def get_price(symbol):
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms=USD"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.content)
        if "USD" in data:
            return data["USD"]
        else:
            return None
    else:
        return None

def start(update, context):
    chat_id = update.effective_chat.id
    message = ""

    crypto_data = get_prices()
    for i in crypto_data:
        coin = crypto_data[i]["coin"]
        price = crypto_data[i]["price"]
        change_day = crypto_data[i]["change_day"]
        change_hour = crypto_data[i]["change_hour"]
        message += f"Token: {coin}\nCena: ${price:,.2f}\nGodzina Zmiana: {change_hour:.3f}%\nDzienna Zmiana: {change_day:.3f}%\n\n"

    context.bot.send_message(chat_id=chat_id, text=message)


dispatcher.add_handler(CommandHandler("raport", start))
updater.start_polling()

# function that takes your message from telegram e.g if you write /eth function takes it and send it to the symbol.
def handle_message(update, context):
    if update.message:
        message = update.message.text
        if message.startswith("/"):
            symbol = message.split(" ")[0][1:].upper()
            price = get_price(symbol)
            if price:
                chat_id = update.message.chat_id
                context.bot.send_message(chat_id=chat_id, text=f"{symbol} ${price}")
                print(f"{symbol} ${price}")
            else:
                chat_id = update.message.chat_id
                context.bot.send_message(chat_id=chat_id, text=f"Przepraszam, nie mogłem znaleźć kryptowaluty, którą napisałeś, proszę napisz jeszcze raz poprawnie albo istnieje szansa, że po prostu nie mam jej w swojej bazie danych.")
        else:
            pass



def show_24_gecko_coins(update, context):
    chat_id = update.effective_chat.id

    views_url_24 = 'https://api.coingecko.com/api/v3/search/trending'
    response = requests.get(views_url_24)
    data = response.json()
    trending_coins = data['coins']
    trending_coins.sort(key=lambda coin: coin['item']['market_cap_rank'])

    message = "<code>Top-7 najpopularniejszych monet na CoinGecko, wyszukiwanych przez użytkowników w ciągu ostatnich 24 godzin (w kolejności od najbardziej popularnej do najmniej popularnej):\n</code>"
    for i, coin in enumerate(trending_coins[:7]):
        name = coin['item']['name']
        symbol = coin['item']['symbol']
        rank = coin['item']['market_cap_rank']

        message += f'{i+1}. {name} ({symbol}) CoinGecko rank:{rank}\n'
        
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

dispatcher.add_handler(CommandHandler("top7", show_24_gecko_coins))
updater.start_polling()





def companies_btc(update, context):
    chat_id = update.effective_chat.id
    url = "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin"

    response = requests.get(url)
    data = response.json()

    message = "<code>udziały spółek publicznych w BTC (uporządkowane według całkowitych udziałów malejąco):\n</code>"
    for company in data["companies"]:
        name = company["name"]
        symbol = company["symbol"]
        country = company["country"]
        total_holdings = company["total_holdings"]

        message += f'<b>Firma:</b> {name}\n'
        message += f'<b>Skrót:</b> {symbol}\n'
        message += f'<b>Kraj:</b> {country}\n'
        message += f'<b>Ilość:</b> {total_holdings} BTC\n\n'

    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

dispatcher.add_handler(CommandHandler("spolki", companies_btc))
updater.start_polling()





# Add the error handler to the dispatcher
dp = updater.dispatcher

# main function.
# remember if bot at the start printing "Timed out, trying again..." please remove your bot from a telegram group.
def main():
    dp.add_handler(telegram.ext.CommandHandler("start", start))
    dp.add_handler(telegram.ext.CommandHandler("top", show_24_gecko_coins))
    dispatcher.add_handler(CommandHandler("spolki", companies_btc))

    dp.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, handle_message))
    asyncio.run(send_message())

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()





'''





asyncio.run(send_message())


'''