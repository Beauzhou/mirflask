from models.post import BoardModel, PostModel
from models.auth import UserModel, RoleModel, Permission
from exts import db
import random


def init_boards():
    board_names = ['Python', 'Flask', 'Django', '爬虫', '前端']
    for index, board_name in enumerate(board_names):
        board = BoardModel(name=board_name, priority=len(board_names)-index)
        db.session.add(board)
    db.session.commit()
    print("板块初始化成功！")


# 0b001
# 0b010
# 0b011 = ob001 | ob010
# 1|0=1,1|1=1,0|0=0

def init_roles():
    # 运营
    operator_role = RoleModel(name="运营", desc="负责管理帖子和评论",
                         permissions=Permission.POST | Permission.COMMENT | Permission.USER)
    # 管理员
    admin_role = RoleModel(name="管理员", desc="负责整个网站的管理",
                      permissions=Permission.POST | Permission.COMMENT | Permission.USER | Permission.STAFF)
    # 开发者（权限是最大的）
    developer_role = RoleModel(name="开发者", desc="负责网站的开发", permissions=Permission.ALL_PERMISSION)

    db.session.add_all([operator_role, admin_role, developer_role])
    db.session.commit()
    print("角色添加成功！")


def init_developor():
    role = RoleModel.query.filter_by(name="开发者").first()
    user = UserModel(username="hynever", email="hynever@qq.com", password='111111', is_staff=True, role=role)
    db.session.add(user)
    db.session.commit()
    print('开发者角色下的用户创建成功！')


def bind_roles():
    user1 = UserModel.query.filter_by(email="hynever@qq.com").first()
    user2 = UserModel.query.filter_by(email="abc@qq.com").first()
    user3 = UserModel.query.filter_by(email="ccc@qq.com").first()

    role1 = RoleModel.query.filter_by(name="开发者").first()
    role2 = RoleModel.query.filter_by(name="运营").first()
    role3 = RoleModel.query.filter_by(name="管理员").first()

    user1.role = role1
    user2.role = role2
    user3.role = role3

    db.session.commit()
    print("用户和角色绑定成功！")


def create_test_posts():
    boards = list(BoardModel.query.all())
    board_count = len(boards)
    for x in range(99):
        title = "我是标题%d"%x
        content = "我是内容%d"%x
        author = UserModel.query.first()
        index = random.randint(0, board_count-1)
        board = boards[index]
        post_model = PostModel(title=title, content=content, author=author,board=board)
        db.session.add(post_model)
    db.session.commit()
    print("测试帖子添加成功")
