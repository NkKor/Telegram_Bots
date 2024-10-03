import os

import requests
import openai
from dotenv import load_dotenv

load_dotenv()

model = 'gpt-4o-mini-2024-07-18'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query, pages=1):
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


def proccess_search_openai(GOOGLE_API_KEY,
                           SEARCH_ENGINE_ID,
                           question,
                           pages=1):
    print('started search...')
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {'role': 'system', 'content': f'generate google search query in english for this question\n'
                                              f'{question}'}
            ],
            max_tokens=20,
            temperature=0.9,
        )
        query = response['choices'][0]['message']['content']
    except Exception as e:
        query = question
    print(query)

    search_res = get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query, pages=pages)

    print(search_res)
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {'role': 'system', 'content': f'Interpret information to suit answer for this question: {question}'},
                {'role': 'system', 'content': search_res},
                {'role': 'system', 'content': 'Write a full and useful answer.'}
            ],
            max_tokens=100,
            temperature=0.9,
        )
        text_response = response['choices'][0]['message']['content']
    except Exception as e:
        text_response = search_res
    print(text_response)
    return text_response

query = "Python await message answer context length"
search_res = get_search_result(GOOGLE_API_KEY, SEARCH_ENGINE_ID, query)

print(search_res)