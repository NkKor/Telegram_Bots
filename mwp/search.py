import os
import requests
import openai
from dotenv import load_dotenv
from mwp.util import get_gpt_response


load_dotenv()
model = 'gpt-4o-mini-2024-07-18'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query, pages=1):
    """
    Функция для обработки запросов на поиска через API Google
    :param GOOGLE_API_KEY: ключ для работы с API поиска от Google
    :param SEARCH_ENGINE_ID: id поисковой машины от Google
    :param query: поисковой запрос
    :param pages:
    :return: res_str - результат поиска в интернете в формате строки
    """
    res_str = ''
    for p in range(1, pages + 1):
        start = (p - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start={start}"
        data = requests.get(url).json()
        search_items = data.get('items')
        for i, search_item in enumerate(search_items, start=1):
            try:
                long_description = search_item["pagemap"]["metatags"][0]["og:description"]
            except KeyError:
                long_description = "N/A"
            title = search_item.get('title')
            snippet = search_item.get('snippet')
            res_str += (f'Result {i}:\n'
                        f'title: {title}\n'
                        f'')
            if long_description != 'N/A':
                res_str += f'Long description: {long_description}\n'
            else:
                res_str += f'description: {snippet}'
            res_str += '\n\n'
    return res_str


def proccess_search_openai(GOOGLE_API_KEY,SEARCH_ENGINE_ID, question, pages=1):
    """
    Функция обработки результатов поиска с помощью OpenAI
    :param GOOGLE_API_KEY: ключ для работы с API поиска от Google
    :param SEARCH_ENGINE_ID: id поисковой машины от Google
    :param question: вопрос для отправки в OpenAI
    :param pages:
    :return:
    """
    context = [
                {'role': 'system', 'content': f'сгенерируй запрос в гугл по этому вопросу: {question}'
                 }
            ]
    response = get_gpt_response(context)

    if response["msg"] == 'Failed':
        query = question
    else:
        query = response["response"].choices[0].message['content']


    search_res = get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query, pages=pages)

    context = [
                {'role': 'system', 'content': f'Интерпретируй информацию для ответа на этот вопрос: {question}'},
                {'role': 'system', 'content': search_res},
                {'role': 'system', 'content': 'Дай полный и полезный ответ.'}
            ]
    final_response = get_gpt_response(context)

    if final_response["msg"] == 'Failed':
        text_response = search_res
    else:
        text_response = final_response["response"].choices[0].message['content']

    return text_response


query = "Python await message answer context length"
search_res = get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query)

print(search_res)