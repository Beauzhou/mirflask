from flask import (
    Blueprint,
    request,
    render_template,
    current_app,
    make_response,
    session,
    redirect,
    g,
    jsonify,
    url_for
)
import string
import random

from flask_mail import Message

from exts import cache, mail
from utils import restful
from utils.captcha import Captcha
import time
import os
from io import BytesIO
from .forms import RegisterForm, LoginForm, UploadImageForm, EditProfileForm, PublicPostForm, PublicCommentForm
from models.auth import UserModel, Permission
from exts import db
from .decorators import login_required
from hashlib import md5
from flask_avatars import Identicon
from models.post import BoardModel, PostModel, CommentModel, BannerModel
from flask_paginate import get_page_parameter, Pagination
from sqlalchemy.sql import func
from flask_jwt_extended import create_access_token


bp = Blueprint("front", __name__, url_prefix="/")


# 钩子函数：before_request，在调用视图函数之前执行
@bp.before_request
def front_before_reuqest():
    if 'user_id' in session:
        user_id = session.get("user_id")
        user = UserModel.query.get(user_id)
        setattr(g, "user", user)

# 请求 => before_request => 视图函数（返回模板） => context_processor => 将context_processor返回的变量也添加到模板中

# 上下文处理器
@bp.context_processor
def front_context_processor():
    if hasattr(g, "user"):
        return {"user": g.user}
    else:
        return {}

@bp.route('/')
def index():
    sort = request.args.get("st", type=int, default=1)
    board_id = request.args.get("bd", type=int, default=None)
    boards = BoardModel.query.order_by(BoardModel.priority.desc()).all()
    post_query = None
    if sort == 1:
        post_query = PostModel.query.order_by(PostModel.create_time.desc())
    else:
        # 根据评论数量进行排序
        post_query = db.session.query(PostModel).outerjoin(CommentModel).group_by(PostModel.id).order_by(func.count(CommentModel.id).desc(), PostModel.create_time.desc())

    page = request.args.get(get_page_parameter(), type=int, default=1)
    # 1：0-9
    # 2：10-19
    start = (page - 1) * current_app.config['PER_PAGE_COUNT']
    end = start + current_app.config['PER_PAGE_COUNT']

    if board_id:
        # "mapped class CommentModel->comment" has no property "board_id"
        # CommentModel中寻找board_id，然后进行过滤
        # post_query = post_query.filter_by(board_id=board_id)
        post_query = post_query.filter(PostModel.board_id==board_id)
    total = post_query.count()
    posts = post_query.slice(start, end)
    pagination = Pagination(bs_version=3, page=page, total=total, prev_label="上一页")

    banners = BannerModel.query.order_by(BannerModel.priority.desc()).all()
    context = {
        "boards": boards,
        "posts": posts,
        "pagination": pagination,
        "st": sort,
        "bd": board_id,
        "banners": banners
    }
    return render_template("front/index.html", **context)


@bp.get('/cms')
def cms():
    return render_template("cms/index.html")

# @bp.get("/email/captcha")
# def email_captcha():
#     # /email/captcha?email=xx@qq.com
#     email = request.args.get("email")
#     if not email:
#         # return jsonify({"code": 400, "message": "请先传入邮箱！"})
#         return restful.params_error(message="请先传入邮箱！")
#     # 随机的六位数字
#     source = list(string.digits)
#     captcha = "".join(random.sample(source, 6))
#     message = Message(subject="【知了传课】注册验证码", recipients=[email], body="【知了传课】您的注册验证码为：%s"%captcha)
#     try:
#         # 发送邮件实际上一个网络请求
#         mail.send(message)
#     except Exception as e:
#         print("邮件发送失败！")
#         print(e)
#         return jsonify({"code": 500, "message": "邮件发送失败！"})
#     return jsonify({"code": 200, "message": "邮件发送成功！"})

@bp.get("/email/captcha")
def email_captcha():
    # /email/captcha?email=xx@qq.com
    email = request.args.get("email")
    if not email:
        return restful.params_error(message="请先传入邮箱！")
    # 随机的六位数字
    source = list(string.digits)
    captcha = "".join(random.sample(source, 6))
    subject="【知了传课】注册验证码"
    body = "【知了传课】您的注册验证码为：%s" % captcha
    current_app.celery.send_task("send_mail", (email, subject, body))
    cache.set(email, captcha)
    print(cache.get(email))
    return restful.ok(message="邮件发送成功！")


@bp.route("/graph/capthca")
def graph_captcha():
    captcha, image = Captcha.gene_graph_captcha()
    # 将验证码存放到缓存中
    # key, value
    # bytes
    key = md5((captcha+str(time.time())).encode('utf-8')).hexdigest()
    cache.set(key, captcha)
    # with open("captcha.png", "wb") as fp:
    #     image.save(fp, "png")
    out = BytesIO()
    image.save(out, "png")
    # 把out的文件指针指向最开的位置
    out.seek(0)
    resp = make_response(out.read())
    resp.content_type = "image/png"
    resp.set_cookie("_graph_captcha_key", key, max_age=3600)
    return resp


@bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("front/login.html")
    else:
        form = LoginForm(request.form)
        if form.validate():
            email = form.email.data
            password = form.password.data
            remember = form.remember.data
            user = UserModel.query.filter_by(email=email).first()
            if not user:
                return restful.params_error("邮箱或密码错误！")
            if not user.check_password(password):
                return restful.params_error("邮箱或密码错误！")
            if not user.is_active:
                return restful.params_error("此用户不可用！")
            session['user_id'] = user.id
            # 如果是员工，才生成token
            token = ""
            permissions = []
            if user.is_staff:
                token = create_access_token(identity=user.id)
                for attr in dir(Permission):
                    if not attr.startswith("_"):
                        permission = getattr(Permission, attr)
                        if user.has_permission(permission):
                            permissions.append(attr.lower())
            if remember == 1:
                # 默认session过期时间，就是只要浏览器关闭了就会过期
                session.permanent = True
            """
            {"avatar":"677d1194c930361e88189b315e4de934.jpg","comments":[],"email":"hynever@qq.com","id":"fiuhqDhK6Wo6Rb9hHc9ffX","is_active":true,"is_staff":true,"join_time":"2021-11-25 15:35:40","posts":[],"signature":"欢饮刚来到知了传课学习Python","username":"zhiliaochuanke"}
            """
            user_dict = user.to_dict()
            user_dict['permissions'] = permissions
            return restful.ok(data={"token": token, "user": user_dict})
        else:
            return restful.params_error(message=form.messages[0])


@bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("front/register.html")
    else:
        form = RegisterForm(request.form)
        if form.validate():
            email = form.email.data
            username = form.username.data
            password = form.password.data
            identicon = Identicon()
            filenames = identicon.generate(text=md5(email.encode("utf-8")).hexdigest())
            avatar = filenames[2]
            user = UserModel(email=email, username=username, password=password, avatar=avatar)
            db.session.add(user)
            db.session.commit()
            return restful.ok()
        else:
            # form.errors中存放了所有的错误信息
            # {'graph_captcha': ['请输入正确长度的图形验证码！', '图形验证码错误！']}
            message = form.messages[0]
            return restful.params_error(message=message)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@bp.route("/setting")
@login_required
def setting():
    email_hash = md5(g.user.email.encode("utf-8")).hexdigest()
    return render_template("front/setting.html", email_hash=email_hash)


@bp.post("/avatar/upload")
@login_required
def upload_avatar():
    form = UploadImageForm(request.files)
    if form.validate():
        image = form.image.data
        # 不要使用用户上传上来的文件名，否则容易被黑客攻击
        filename = image.filename
        # xxx.png,xx.jpeg
        _, ext = os.path.splitext(filename)
        filename = md5((g.user.email + str(time.time())).encode("utf-8")).hexdigest() + ext
        image_path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
        image.save(image_path)
        # 看个人需求，是否图片上传完成后要立马修改用户的头像字段
        g.user.avatar = filename
        db.session.commit()
        return restful.ok(data={"avatar": filename})
    else:
        message = form.messages[0]
        return restful.params_error(message=message)


@bp.post("/profile/edit")
@login_required
def edit_profile():
    form = EditProfileForm(request.form)
    if form.validate():
        signature = form.signature.data
        g.user.signature = signature
        db.session.commit()
        return restful.ok()
    else:
        return restful.params_error(message=form.messages[0])


@bp.route("/post/public", methods=['GET', 'POST'])
@login_required
def public_post():
    if request.method == 'GET':
        boards = BoardModel.query.order_by(BoardModel.priority.desc()).all()
        return render_template("front/public_post.html", boards=boards)
    else:
        form = PublicPostForm(request.form)
        if form.validate():
            title = form.title.data
            content = form.content.data
            board_id = form.board_id.data
            try:
                # get方法：接收一个id作为参数，如果找到了，那么会返回这条数据
                # 如果没有找到，那么会抛出异常
                board = BoardModel.query.get(board_id)
            except Exception as e:
                return restful.params_error(message="板块不存在！")
            post_model = PostModel(title=title, content=content, board=board, author=g.user)
            db.session.add(post_model)
            db.session.commit()
            return restful.ok(data={"id": post_model.id})
        else:
            return restful.params_error(message=form.messages[0])



@bp.post("/post/image/upload")
@login_required
def upload_post_image():
    form = UploadImageForm(request.files)
    if form.validate():
        image = form.image.data
        # 不要使用用户上传上来的文件名，否则容易被黑客攻击
        filename = image.filename
        # xxx.png,xx.jpeg
        _, ext = os.path.splitext(filename)
        filename = md5((g.user.email + str(time.time())).encode("utf-8")).hexdigest() + ext
        image_path = os.path.join(current_app.config['POST_IMAGE_SAVE_PATH'], filename)
        image.save(image_path)
        # {"data","code", "message"}
        return jsonify({"errno": 0, "data": [{
            "url": url_for("media.get_post_image", filename=filename),
            "alt": filename,
            "href": ""
        }]})
    else:
        message = form.messages[0]
        return restful.params_error(message=message)


@bp.get("/post/detail/<post_id>")
def post_detail(post_id):
    post_model = PostModel.query.get(post_id)
    comment_count = CommentModel.query.filter_by(post_id=post_id).count()
    context = {
        "comment_count": comment_count,
        "post": post_model
    }
    return render_template("front/post_detail.html", **context)


@bp.post("/comment")
@login_required
def public_comment():
    form = PublicCommentForm(request.form)
    if form.validate():
        content = form.content.data
        post_id = form.post_id.data
        try:
            post_model = PostModel.query.get(post_id)
        except Exception as e:
            return restful.params_error(message="帖子不存在！")
        comment = CommentModel(content=content, post_id=post_id, author_id=g.user.id)
        db.session.add(comment)
        db.session.commit()
        return restful.ok()
    else:
        message = form.messages[0]
        return restful.params_error(message=message)