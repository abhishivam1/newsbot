import telebot
import requests
from telebot import types

TOKEN = '6970897422:AAEUX125Om2rs1CHTBXU5b8i4Ho21V2WFkM'
bot = telebot.TeleBot(TOKEN)

topics = [
    "blockchain", "ipo", "financial_markets", "mergers_and_acquisitions",
    "economy_fiscal", "economy_monetary", "economy_macro", "finance",
    "life_sciences", "manufacturing", "real_estate", "retail_wholesale", "technology"
]

def fetch_news(topic):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'NEWS_SENTIMENT',
        'apikey': 'MBMA7UTLLNQWONWG',
        'topics': topic,
    }
    r = requests.get(url, params=params)
    if r.status_code == 200 and 'feed' in r.json():
        feed = r.json()["feed"]
        news_items = [{
            'title': item['title'],
            'url': item['url'],
            'summary': item.get('summary', '')
        } for item in feed[:15]]
        return news_items
    else:
        return None

def send_news_item(chat_id, news_items, topic, index=0, message_id=None):
    item = news_items[index]
    message_text = (
        f"\n"
        f" <b>Headline:</b> {item['title']}\n\n"
        f" <b>URL:</b> <a href='{item['url']}'>{item['url']}</a>\n"
        f"\n"
        f" <b>Summary:</b> {item['summary']}\n"
        f"\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    if index > 0:
        markup.add(types.InlineKeyboardButton("Back", callback_data=f"news_{index-1}_{topic}"))
    if index < len(news_items) - 1:
        markup.add(types.InlineKeyboardButton("Next", callback_data=f"news_{index+1}_{topic}"))
    
    if message_id is None:
        bot.send_message(chat_id, message_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)

def create_topic_markup(page=0, topics_per_page=8):
    markup = types.InlineKeyboardMarkup(row_width=2)  # Set row width to 2 for a 2x2 grid
    start = page * topics_per_page
    end = start + topics_per_page
    topic_buttons = []

    for topic in topics[start:end]:
        topic_buttons.append(types.InlineKeyboardButton(topic.replace("_", " ").title(), callback_data=f"topic_{topic}"))

    # Split the buttons into rows of 2
    for row in [topic_buttons[i:i+2] for i in range(0, len(topic_buttons), 2)]:
        markup.row(*row)

    # Pagination buttons
    row = []
    if start > 0:
        row.append(types.InlineKeyboardButton("Back", callback_data=f"page_{page-1}"))
    if end < len(topics):
        row.append(types.InlineKeyboardButton("Next", callback_data=f"page_{page+1}"))
    if row:
        markup.row(*row)

    return markup

@bot.message_handler(commands=['topic'])
def select_topic(message):
    markup = create_topic_markup()
    bot.send_message(message.chat.id, "Select a topic:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('topic_'))
def topic_selected(call):
    topic = call.data.split('_')[1]
    # Delete the "Choose a topic" message
    bot.delete_message(call.message.chat.id, call.message.message_id)

    news_items = fetch_news(topic)
    if news_items:
        send_news_item(call.message.chat.id, news_items, topic, 0)
    else:
        bot.send_message(call.message.chat.id, "Failed to fetch news for the selected topic.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def change_page(call):
    page = int(call.data.split('_')[1])
    markup = create_topic_markup(page=page)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Select a topic:", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('news_'))
def handle_news_navigation(call):
    parts = call.data.split('_')
    index = int(parts[1])
    topic = parts[2]
    news_items = fetch_news(topic)  # Fetch news items for the topic again

    # Ensure index is within the bounds of news_items
    if index < 0:
        index = 0  # Reset to first item if index is negative
    elif index >= len(news_items):
        index = len(news_items) - 1  # Set to last item if index is too high

    if news_items:
        send_news_item(call.message.chat.id, news_items, topic, index, call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, "Failed to fetch news for the selected topic.")
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    bot.polling()
