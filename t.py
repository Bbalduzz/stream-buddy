# token = "6847505082:AAHvU_mc5zV8g6yMPMdr0r_ZXyMtBJqr4PA"

# import telebot
# import requests, json
# from telethon import TelegramClient, events, sync

# BOT_TOKEN = "6847505082:AAHvU_mc5zV8g6yMPMdr0r_ZXyMtBJqr4PA"
# api_id = '18850584'  # Replace with your API ID
# api_hash = 'b6e3043520f599594984e6f2e672ef42' # Replace with your API hash
# bot_username = 'BelloFigoIlRobot'  # Replace with the bot token

# bot = telebot.TeleBot(BOT_TOKEN)
# client = TelegramClient('custom_session', api_id, api_hash)

# @bot.message_handler(commands=['domain', 'd'])
# def get_domain(message):
# 	# The message you want to send
# 	message_to_send = "Hello, Bot!"

# 	@client.on(events.NewMessage(chats=bot_username))
# 	async def handler(event):
# 	    if event.is_private and event.chat.username == bot_username:
# 	        # print(event.text)
# 	        bot.reply_to(message, event.text)

# 	async def send_message():
# 	    await client.send_message(bot_username, message_to_send)

# 	# Start the client and send a message

# bot.infinity_polling()
# with client:
# 	client.loop.run_until_complete(send_message())
# 	client.run_until_disconnected()

import telebot
from telethon import TelegramClient, events
import threading, asyncio

BOT_TOKEN = "6847505082:AAHvU_mc5zV8g6yMPMdr0r_ZXyMtBJqr4PA"
api_id = '18850584'  # Replace with your API ID
api_hash = 'b6e3043520f599594984e6f2e672ef42' # Replace with your API hash
bot_username = 'BelloFigoIlRobot'  # Replace with the bot token

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient('custom_session', api_id, api_hash)


def start_telethon():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_client():
        await client.start()

        @client.on(events.NewMessage(chats=bot_username))
        async def handler(event):
            if event.is_private and event.chat.username == bot_username:
                print(event.text)
                bot.send_message(message.chat.id, event.text)

        await client.run_until_disconnected()

    loop.run_until_complete(run_client())
    return loop

@bot.message_handler(commands=['domain', 'd'])
def get_domain(message):
    async def send_message():
        await client.send_message(bot_username, "Hello, Bot!")

    # Run the send_message coroutine in the Telethon event loop
    asyncio.run_coroutine_threadsafe(send_message(), telethon_loop)

# Start Telethon client in a separate thread
telethon_thread = threading.Thread(target=start_telethon)
telethon_thread.start()
telethon_loop = telethon_thread.join()

# Start Telebot polling
bot.infinity_polling()


# from telethon import TelegramClient, events, sync

# api_id = '18850584'  # Replace with your API ID
# api_hash = 'b6e3043520f599594984e6f2e672ef42' # Replace with your API hash
# bot_username = 'BelloFigoIlRobot'  # Replace with the bot token

# # The message you want to send
# message_to_send = "Hello, Bot!"

# # Initialize the client
# client = TelegramClient('custom_session', api_id, api_hash)

# @client.on(events.NewMessage(chats=bot_username))
# async def handler(event):
#     if event.is_private and event.chat.username == bot_username:
#         print(event.text)

# async def send_message():
#     await client.send_message(bot_username, message_to_send)

# # Start the client and send a message
# with client:
#     client.loop.run_until_complete(send_message())
#     client.run_until_disconnected()

