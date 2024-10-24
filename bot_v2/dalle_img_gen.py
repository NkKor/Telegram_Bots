import dotenv
import openai
from openai import OpenAI
import requests


dotenv.load_dotenv()
client = OpenAI()


def generate_image_variation(img_file, user_id, size="512x512", num=1):
    img_response = openai.Image.create_variation(
        image=img_file,
        n=num,
        size=size
    )
    img_url = img_response['data'][0]['url']
    # image_paths = [f"generated/{i}_generated.png" for i in range(num)]
    return img_url


def generate_image(description, user_id, num=1):
    img_response = client.images.generate(
        model="dall-e-2",
        prompt=description,
        n=num,
        size="512x512"
    )
    img_links = [img_response.data[i].url for i in range(num)]
    image_path = []
    for i in range(0, len(img_links)):
        new_path = f"generated/{user_id}_{i}_generated.png"
        image_path.append(new_path)
        with open(new_path, "wb") as f:
            f.write(requests.get(img_links[i]).content)
    return img_links


def d3_image_generate(description, user_id, num=1):
    img_response = client.images.generate(
        model="dall-e-3",
        prompt=description,
        size="1024x1024",
        quality="standard",
        n=num,
    )
    img_links = [img_response.data[i].url for i in range(num)]
    image_path = []
    for i in range(0, len(img_links)):
        new_path = f"generated/{user_id}_{i}_generated.png"
        image_path.append(new_path)
        with open(new_path, "wb") as f:
            f.write(requests.get(img_links[i]).content)
    return img_links


def d2_image_variate(user_id, num=1):
    response = client.images.create_variation(
        model="dall-e-2",
        image=open("hr_bot/generated/0_generated.png", "rb"),
        size="1024x1024",
        n=num,
    )
    image_url = response.data[0].url
    return image_url


def d2_image_edit(description, user_id, size="1024x1024", num=1):
    response = client.images.edit(
        model="dall-e-2",
        image=open("hr_bot/generated/0_generated.png", "rb"),
        mask=open("hr_bot/generated/mask.png", "rb"),
        prompt=description,
        size="1024x1024",
        n=num,
    )
    image_url = response.data[0].url
    return image_url