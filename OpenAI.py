import openai
import os
import dotenv
import pandas as pd
import json


dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_TOKEN")

# context = [{"role": "system", "content": "Отвечай как мудрый дух ворона из иной реальности"}]

try:
    users_list = pd.read_csv("users.csv", index_col= "chat")
except FileNotFoundError:
    users_list = pd.DataFrame(columns=["context"])
    users_list.index.name = "chat"
    users_list.to_csv("users.csv")

chat = input("Chat name:")
if chat not in users_list.index:
    users_list.loc[chat] = ["[]"]

while True:

    reqest = input()
    if reqest == "выход":
        break

    context = json.loads(users_list.loc[chat, "context"])
    context.append({"role": "user", "content": reqest})
    context.insert(0, {"role": "system", "content": "Отвечай как пират"})

    context.append({"role": "user", "content": reqest}) # system, user, assistant
    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-08-06",
        messages=context,
        max_tokens=50,
        temperature=0.7
    )
    ai_response = response['choices'][0]['message']['content']
    context.append({"role": "assistant", "content": ai_response})
    users_list.at[chat,"context"] = json.dumps(context)

    print(f"ChatGPT:{ai_response}")
users_list.to_csv("users.csv")