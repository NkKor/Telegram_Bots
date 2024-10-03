import os
import openai
from dotenv import load_dotenv
import requests


load_dotenv()
model = "gpt-4-mini"


def get_search_results(GOOGLE_API_TOKEN, SEARCH_ENGINE_ID, query, pages=1):
    res = ''
    for i in range(pages):
        start = (i-1)*10 + 1
        url = (f'https://www.googleapis.com/customsearch/v1?'
               f'key={GOOGLE_API_TOKEN}'
               f'&cx={SEARCH_ENGINE_ID}'
               f'&q={query}'
               f'&start={start}')
        response = requests.get(url).json()
        search_items = response.get('items')
        for item, search_item in enumerate(search_items, pages):
            try:
                long_description = search_item['pagemap']['metatags'][0]['pg:description']
            except KeyError:
                long_description = 'N/A'
            title = search_item.get('title')
            snippet = search_item.get('snippet')
            res = (f'Result {item}:\n'
                   f'title: {title}\n')
            if long_description != 'N/A':
                res += f'long_description: {long_description}\n'
            else:
                res += f'description: {snippet}\n'
            res += '\n\n'
    return res


def process_search_openai(GOOGLE_API_TOKEN, SEARCH_ENGINE_ID, question, pages=1):
    response = openai.ChatCompletion.create(
        engine=model,
        messages=[{"role": "system", "content": f"generate google search query for this question\n"
                                                f"{question}"}
                  ],
        max_tokens=100,
        temperature=0.9

    )
    query = response['choices'][0]['message']['content']
    search_result = get_search_results(GOOGLE_API_TOKEN, SEARCH_ENGINE_ID, query, pages)
    response = openai.ChatCompletion.create(
        engine=model,
        messages=[{"role": "system", "content": f"interpret information to suit answer for this question\n {question}"},
                  {"role": "system", "content": search_result}
                  ],
        max_tokens=5000,
        temperature=0.9
    )
    text_response = response['choices'][0]['message']['content']
    return text_response
