import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm
import os


engine = _sql.create_engine(os.getenv('DATABASE_URL'))

SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = _sql.orm.declarative_base()


def add_tables():
    return Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


try:
    with engine.connect() as connection:
        print("Connection successful")
except Exception as e:
    print("Connection failed:", e)
