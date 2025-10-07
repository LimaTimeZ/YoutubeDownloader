import os

REDIS_URL = os.environ.get("REDIS_URL")
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
API_KEY = os.environ.get("API_KEY", "Realne$$")