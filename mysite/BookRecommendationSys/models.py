import datetime

from django.db import models
from django.db.models import ForeignKey


# Create your models here.

class Book(models.Model): # 图书模型
    ISBN = models.CharField(max_length=13, unique=True, primary_key=True) # 主键
    BookTitle = models.CharField(max_length=255) # 书名
    BookAuthor = models.CharField(max_length=255) # 作者
    keyword = models.CharField(max_length=255) # PS:关键字通过逗号隔开
    description = models.TextField(default="该书暂无详情") # 书籍描述
    YearOfPublication = models.IntegerField() # 出版年份
    Publisher = models.CharField(max_length=120) # 出版商
    imageURL = models.URLField() # 图书图片的URL
    score = models.FloatField(default=0) # 图书评分

    def __str__(self):
        return self.BookTitle

class User(models.Model): # 用户模型
    userID = models.BigAutoField(primary_key=True, auto_created=True) # 用户ID
    name = models.CharField(max_length=20) # 用户名
    email = models.EmailField() # 注册邮箱
    sex = models.CharField(max_length=4) # 男或女
    sign = models.CharField(max_length=50) # 个性签名
    pwd = models.CharField(max_length=20) # 密码
    birthday = models.DateField(blank=True) # 生日
    signupDate = models.DateField(auto_now_add=True) # 注册日期
    avatar_path = models.FilePathField(null=True) # 用户头像路径
    fans = models.IntegerField(default=0) # 粉丝数
    ding = models.IntegerField(default=0) # 赞数

    def __str__(self):
        return self.name

# 书评
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField() # 内容
    create_time = models.DateTimeField(auto_now_add=True)
    star = models.FloatField(default=0) # 评分
    zan = models.IntegerField(default=0)  # 赞数
    zan_user = models.TextField(default='[]') # 赞的用户

class BookList(models.Model): # 书单模型
    bookListId = models.BigAutoField(primary_key=True)
    bookListTitle = models.CharField(max_length=255, default='我的书单') # 书单名
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 外键
    description = models.TextField()  # 书单描述
    bookList = models.TextField(blank=True) # 通过字符串来存储书单中书本的ISBN
    create_time = models.DateTimeField(auto_now_add=True)  # 创建时间
    fans = models.IntegerField(default=0) # 关注人数
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.bookListId

class FollowBookListGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 用户
    book_list = models.TextField(blank=True) # '[]' 存储bookListId

# 权限
class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tokenComment = models.BooleanField(default=True) # 评论权
    tokenPublic = models.BooleanField(default=True) # 公开数据权
    tokenLogin = models.BooleanField(default=True)  # 登录权

    def __str__(self):
        return self.user.userID

# 通过Group 和 GroupList 构成好友系统
class Group(models.Model): # 群组
    groupID = models.BigAutoField(primary_key=True, auto_created=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # ups = '[1, 2, 3, ...]'
    ups = models.TextField(blank=True)  # 好友列表 以用户ID字符形式

    def __str__(self):
        return self.groupID


class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listName = models.CharField(max_length=120) # 喜爱列表名
    isOpen = models.BooleanField(default=True) # 是否公开
    bookList = models.TextField(blank=True)
    numOfBooks = models.BigIntegerField(default=0) # 喜欢数目

# 论坛
class Forum(models.Model):
    id = models.BigAutoField(primary_key=True) # 帖子id
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 帖子发起者
    title = models.CharField(max_length=120) # 标题
    content = models.TextField(blank=True) # 内容
    addTime = models.DateTimeField(auto_now_add=True) # 发布时间
    ding = models.IntegerField(default=0) # 点赞数
    ding_user = models.TextField(default='[]')  # 点赞的人
    numComm = models.IntegerField(default=0) # 评论数(热度）
    is_public = models.BooleanField(default=True)  # 是否公开

# 评论
class Comment(models.Model):
    id = models.BigAutoField(primary_key=True, auto_created=True)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=400) # 评论内容
    addTime = models.DateTimeField(auto_now_add=True) #评论时间
    ding = models.IntegerField(default=0) # 赞数
    ding_user = models.TextField(default='[]') # 点赞的人

    def __str__(self):
        return self.id

# 管理
class Admin(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30)
    pwd = models.CharField(max_length=20)
    email = models.EmailField()
    addTime = models.DateTimeField(auto_now_add=True)

# 反馈(供关联用户和管理员查看）
class Feedback(models.Model):
    id = models.BigAutoField(primary_key=True)
    addTime = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=120) #标题
    description = models.TextField() #内容
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 发布用户
    admin_id = models.IntegerField(default=0) # 管理员
    replyInformation = models.TextField(blank=True) # 回复信息
    replyTime = models.DateTimeField(default='1970-1-1') # 回复时间
    checkStatus = models.BooleanField(default=False) # 处理状态

class History(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_history = models.CharField(max_length=1000, default='[]') # '[]' 存储搜索历史, 使用最近时间的10个条目
    book_history = models.CharField(max_length=250, default='[]') # '[]' 存储访问书籍历史，使用最近时间的10个条目