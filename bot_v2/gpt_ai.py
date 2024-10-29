import tdata as td
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
gpt_model = 'gpt-4o-mini-2024-07-18'
gpt_sufix = "Use a required formay so that your answer can be parsed"
gpt_prefix = ('Answer short and useful. Use json format '
                  '{"text": "your_answer",'
                  '"image": "your prompt for arised picture"}')


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

    response = client.chat.completions.create(
        model=model,
        messages=[
                {"role": "system", "content": gpt_prefix},
                {"role": "user", "content": context},
                {"role": "system", "content": gpt_sufix},
            ],
        temperature=temperature,
        max_tokens=max_tokens,
        n=1
    )

    return response
