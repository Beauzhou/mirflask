import os
from datetime import timedelta

SECRET_KEY = "dfasdfsdflasdjfl"

# 项目根路径
BASE_DIR = os.path.dirname(__file__)

DB_USERNAME = 'root'
DB_PASSWORD = '980505'
DB_HOST = '127.0.0.1'
DB_PORT = '3306'
DB_NAME = 'mirflask'

# session.permanent=True的情况下的过期时间
PERMANENT_SESSION_LIFETIME = timedelta(days=7)


DB_URI = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4' % (DB_USERNAME,DB_PASSWORD,DB_HOST,DB_PORT,DB_NAME)

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False


# antdxatjmrwbdbeh
# MAIL_USE_TLS：端口号587
# MAIL_USE_SSL：端口号465
# QQ邮箱不支持非加密方式发送邮件
# 发送者邮箱的服务器地址
MAIL_SERVER = "smtp.163.com"
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_DEBUG = True
MAIL_USERNAME = "zhoubo1035@163.com"
MAIL_PASSWORD = "BLWCKTDUWTJGESKS"
MAIL_DEFAULT_SENDER = "zhoubo1035@163.com"

# Celery的redis配置
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

# Flask-Caching的配置
CACHE_TYPE = "RedisCache"
CACHE_DEFAULT_TIMEOUT = 300
CACHE_REDIS_HOST = "127.0.0.1"
CACHE_REDIS_PORT = 6379

# 头像配置
AVATARS_SAVE_PATH = os.path.join(BASE_DIR, "media", "avatars")
# 帖子图片存放路径
POST_IMAGE_SAVE_PATH = os.path.join(BASE_DIR, "media", "post")
# 轮播图图片存放路径
BANNER_IMAGE_SAVE_PATH = os.path.join(BASE_DIR, "media", "banner")

# 每页展示帖子的数量
PER_PAGE_COUNT = 10

# 设置JWT过期时间
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=100)