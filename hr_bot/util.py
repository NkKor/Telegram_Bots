import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
gpt_model = 'gpt-4o-mini-2024-07-18'


def get_gpt_response(context, model=gpt_model, max_tokens=1000, temperature=0.7, n=1):
    """
    Функция для обработки сообщений пользователя через GPT от OpenAI
    :param context: контекст диалога, сохраняется в отдельном файле в формате JSON
    :param model: модель ChatGPT от OpenAI
    :param max_tokens: максимальное количество токенов
    :param temperature: степень правдивости нейросети при ответе
    :param n:
    :return:
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=context,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1
        )
    except Exception as e:
        return {'msg': 'Failed',
                'response': str(e)}

    return {'msg': 'Success',
            'response': response}
