import sqlalchemy as sql
import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
import dotenv
import os
from aiogram import Dispatcher
import prep
# from prep.database import engine


dotenv.load_dotenv()
TOKEN=os.getenv('TELEGRAM_API_TOKEN')
engine = sql.create_engine(os.getenv('DATABASE_URL'))

Base = sql.orm.declarative_base()
SessionLocal = orm.sessionmaker(bind=engine)

try:
    with engine.connect() as connection:
        print("Connection successful")
except Exception as e:
    print("Connection failed:", e)
