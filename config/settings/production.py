# settings/production.py

from .base import *
import os
from decouple import config
import environ

import dj_database_url

DEBUG = False

DEBUG = os.environ.get("DEBUG", "False") == "True"

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")

ALLOWED_HOSTS = ["*"]

# CSRF Settings
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")  # ensure at top

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Need to add url of endpoint and frontend
CSRF_TRUSTED_ORIGINS = [
    "https://thefoundrykitchen.co.uk",
    "https://www.thefoundrykitchen.co.uk",
    "https://the-foundry-frontend.vercel.app",
]

# Allow your Vercel frontend
CORS_ALLOWED_ORIGINS = [
    "https://thefoundrykitchen.co.uk",
    "https://www.thefoundrykitchen.co.uk",
    "https://the-foundry-frontend.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Postgresql & Env Variable
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('PGDATABASE'),
        'USER': env('PGUSER'),
        'PASSWORD': env('PGPASSWORD'),
        'HOST': env('PGHOST'),
        'PORT': env('PGPORT'),
    }
}

# CHANNEL_LAYERS = {
    # "default": {
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {
            # "hosts": [REDIS_URL],
        # },
    # },
# }

# # Cloudinary - Images
# # Cloudinary config
# CLOUDINARY_STORAGE = {
    # 'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
    # 'API_KEY': env('CLOUDINARY_API_KEY'),
    # 'API_SECRET': env('CLOUDINARY_API_SECRET'),
# }


# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
