from db_conf import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
