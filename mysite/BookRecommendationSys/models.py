import datetime

from django.db import models

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

class BookList(models.Model): # 书单模型
    bookListId = models.BigAutoField(primary_key=True)
    bookListTitle = models.CharField(max_length=255, default='我的书单') # 书单名
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 外键
    description = models.TextField()  # 书单描述
    bookList = models.TextField(blank=True) # 通过字符串来存储书单中书本的ISBN
    create_time = models.DateTimeField(auto_now_add=True)  # 创建时间
    fans = models.IntegerField(default=0) # 关注人数
    def __str__(self):
        return self.bookListId

# 权限
class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tokenPublish = models.BooleanField(default=True) # 发布帖子或评论权限
    tokenCommunication = models.BooleanField(default=True) # 是否被禁言
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

# 评论
class Comments(models.Model):
    commentID = models.BigAutoField(primary_key=True, auto_created=True)
    ForumID = models.BigIntegerField() # 评论的帖子的ID
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=400) # 评论内容
    objectID = models.BigIntegerField(blank=True) # 评论的对象ID
    addTime = models.DateTimeField(auto_now_add=True) #评论时间

    def __str__(self):
        return self.commentID

class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listName = models.CharField(max_length=120) # 喜爱列表名
    isOpen = models.BooleanField(default=True) # 是否公开
    bookList = models.TextField(blank=True)
    numOfBooks = models.BigIntegerField(default=0) # 喜欢数目

# 论坛
class Forums(models.Model):
    id = models.BigAutoField(primary_key=True) # 帖子id
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 帖子发起者
    detail = models.TextField(blank=True) # 内容
    addTime = models.DateTimeField(auto_now_add=True) # 发布时间
    ding = models.IntegerField(default=0) # 点赞数
    numComm = models.IntegerField(default=0) # 评论数
    link = models.CharField(max_length=200, blank=True) # 关联链接

# 管理
class Admins(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30)
    pwd = models.CharField(max_length=20)
    email = models.EmailField()
    addTime = models.DateTimeField(auto_now_add=True)

# 反馈(供关联用户和管理员查看）
class Feedbacks(models.Model):
    id = models.BigAutoField(primary_key=True)
    addTime = models.DateTimeField(auto_now_add=True)
    description = models.TextField() #内容
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 发布用户
    admin = models.ForeignKey(Admins, on_delete=models.CASCADE) # 管理员
    replyInformation = models.TextField(blank=True) # 回复信息
    checkStatus = models.BooleanField(default=False) # 处理状态

# 用户会话 Session
class Sessions(models.Model):
    session_id = models.BigAutoField(primary_key=True)
    last_time = models.DateTimeField(auto_now_add=True)
    userAID = models.BigIntegerField() # 发起者
    userBID = models.BigIntegerField() # 接受者
    last_message_id = models.BigIntegerField()  # 该会话最后一条信息的id

class Message(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    from_session = models.ForeignKey(Sessions, on_delete=models.CASCADE)  # 所属于的session
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 所属于的user
    time = models.DateTimeField(auto_now_add=True)
    description = models.TextField() # 信息内容
    last_message_id = models.BigIntegerField() # 上一条信息的id
