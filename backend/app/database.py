from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Altere 'root:senha' pelas credenciais locais do seu MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:senha@localhost/wilderfeast_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Injeção de dependência para abrir e fechar a sessão do banco por requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()