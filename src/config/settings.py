import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

ENV_CST = os.environ.get("ENV_CST")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://YOUR-PROJECT.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "EDIT_ME")
SUPABASE_SCHEMA = os.environ.get("SUPABASE_SCHEMA", "public")
SUPABASE_FUNDS_TABLE = os.environ.get("SUPABASE_FUNDS_TABLE", "blackrock_funds")
SUPABASE_INSERT_BATCH_SIZE = int(os.environ.get("SUPABASE_INSERT_BATCH_SIZE", "500"))
