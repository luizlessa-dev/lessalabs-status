import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

NOMINATIM_USER_AGENT = "valorreal-pipeline/0.1 (contact@valorreal.com.br)"

CITIES = {
    "sao-paulo": {
        "name": "São Paulo",
        "db_id": 1,
        "downloader": "sao_paulo",
    },
    "rio-de-janeiro": {
        "name": "Rio de Janeiro",
        "db_id": 2,
        "downloader": "rio_de_janeiro",
    },
    "belo-horizonte": {
        "name": "Belo Horizonte",
        "db_id": 3,
        "downloader": "belo_horizonte",
    },
    "porto-alegre": {
        "name": "Porto Alegre",
        "db_id": 4,
        "downloader": "porto_alegre",
    },
}
