from flask import Flask
import config
from exts import db, mail, cache, csrf, avatars, jwt, cors
from flask_migrate import Migrate
from models import auth
from apps.front import front_bp
from apps.media import media_bp
from apps.cmsapi import cmsapi_bp
from bbs_celery import make_celery
import commands

# 将ORM模型映射到数据库中三部曲
# 0. migrate = Migrate(app,db)
# 1. 初始化迁移仓库：flask db init
# 2. 将orm模型生成迁移脚本：flask db migrate
# 3. 运行迁移脚本，生成表：flask db upgrade

# Python中操作redis安装两个包：
# 1. pip install redis
# 2. pip install hiredis

# 在windows上使用celery，需要借助gevnet
# pip install gevent
# celery -A app.mycelery --loglevel=info -P gevent

# pip install flask-wtf

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)
mail.init_app(app)
cache.init_app(app)
csrf.init_app(app)
avatars.init_app(app)
jwt.init_app(app)
cors.init_app(app, resources={r"/cmsapi/*": {"origins": "*"}})

# 排除cmsapi的csrf验证
csrf.exempt(cmsapi_bp)

migrate = Migrate(app, db)

mycelery = make_celery(app)


# 注册蓝图
app.register_blueprint(front_bp)
app.register_blueprint(media_bp)
app.register_blueprint(cmsapi_bp)


# 注册命令
app.cli.command("init_boards")(commands.init_boards)
app.cli.command("init_roles")(commands.init_roles)
app.cli.command("init_developor")(commands.init_developor)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
