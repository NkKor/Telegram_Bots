import requests
import pandas as pd
from dotenv import load_dotenv
import os


load_dotenv()
ninja_key = os.getenv('NINJA_API_KEY')

def get_city_geo(city_name:str):
    url = f"https://api.api-ninjas.com/v1/geocoding?city={city_name}"
    headers = {
        "X-Api-Key": ninja_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    else:
        data = response.json()
        if data:
            longitude = data[0]['longitude']
            latitude = data[0]['latitude']

            return longitude, latitude

def save_geo_to_file(city, coordinates):
    filename = "city_coordinates.csv"
    new_city = pd.DataFrame({'city': [city], 'longitude': [coordinates[0]], 'latitude': [coordinates[1]]})
    if os.path.exists(filename):
        cities_df = pd.read_csv(filename,index_col='city')
        if not city in cities_df['city'].values:
            new_city.to_csv(filename, mode='a', index=False, header=False)
    else:
        new_city.to_csv(filename, index=False)


city_name = 'Barnaul'
save_geo_to_file(city_name, get_city_geo(city_name))