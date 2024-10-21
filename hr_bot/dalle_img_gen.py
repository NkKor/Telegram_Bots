import os
from dotenv import load_dotenv
import openai
import requests

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_image_variation(img_file, user_id, size="512x512", num=1):
    img_response = openai.Image.create_variation(
        image=img_file,
        n=num,
        size=size
    )
    img_url = img_response['data'][0]['url']
    # image_paths = [f"generated/{i}_generated.png" for i in range(num)]
    return img_url


def generate_image(description, user_id, size="512x512", num=1):
    img_response = openai.Image.create(
        prompt=description,
        n=num,
        size=size
    )
    img_links = [img_response['data'][i]['url'] for i in range(num)]
    for i in range(0, len(img_links)):
        with open(f"generated/{user_id}{i}_generated.png", "wb") as f:
            f.write(requests.get(img_links[i]).content)
    image_paths = [f"generated/{i}_generated.png" for i in range(num)]
    return image_paths
