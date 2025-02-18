import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import loader, render, redirect
from django.views.decorators.csrf import csrf_exempt

from . import models
# Create your views here.

def index(request, userid):
    return render(request, 'index.html')

def login(request):
    if request.method != 'POST':
        return render(request, "login.html")
    userID = request.POST['userID']
    password = request.POST['password']
    if password == models.User.objects.all().get(userID=userID).pwd:
        return user_home(request, userID)
    return render(request, "login.html")

def generate_group(user_id): # 生成初始group
    group = models.Group(groupName='我的好友', friends='[]')
    models.GroupList.objects.create(userID_id=user_id, groupList='[{0}]'.format(group.groupID))
    group.save()

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        if not models.User.objects.filter(name=username).exists():
            # 生成用户个人信息
            email = request.POST['email']
            password = request.POST['password']
            sign="你好，我是{0}，欢迎来到我的阅读空间".format(username) # 默认值
            sex="男" # 默认值
            path= "img/user_head/default.jpg"
            user = models.User(name=username, email=email, pwd=password, birthday=datetime.date(1975, 1, 1), sign=sign, sex=sex, avatar_path=path)
            user.save()

            # 生成好友群组
            generate_group(user.userID)
            return render(request, "index.html")
    return render(request, "register.html")

# 用户空间
def total_ding(request, userid):
    forum_list = models.Forums.objects.filter(userID_id=userid)
    if not forum_list.exists():
        return 0
    ans = 0
    for forum in forum_list:
        ans = ans + forum.ding
    return ans


# 算是一种对数据库中存储字符串的解释
def get_id_from_list(group_list): # 输出字符串列表中的所有id
    # example:
    # >> group_list
    # >> "[1001, 1002, 1003]"
    group_id_list = []
    group_id = 0
    for c in group_list:
        if (c == ',' or c == ']') and group_id:
            group_id_list.append(group_id)
            group_id = 0
        elif '0' <= c <= '9':
            group_id = 10 * group_id + int(c)
    return group_id_list

def all_friends(request, userid): # 输出所有好友id
    group_list = models.GroupList.objects.get(userID_id=userid)
    friends = [] # 存储好友id
    for group_id in get_id_from_list(group_list.groupList):
        group = models.Group.objects.get(groupID=group_id)
        friends.append(get_id_from_list(group.friends))
    return friends

def get_fans(userid):
    fans = models.User.objects.get(userID=userid).fans
    if fans < 1e6:
        return str(fans)
    elif fans < 1e9:
        return '{0}.{1}万'.format(int(fans/1e5), int(fans / 1e4) % 10)
    else: # 亿级单位
        return '{0}.{1}亿'.format(int(fans/1e9), int(fans / 1e8) % 10)

def user_home(request, userid):
    if userid :
        user = models.User.objects.get(userID=userid)

        return render(request, "home.html", {
            "user": user,
            "ding": total_ding(request, userid),
            "num_friends": len(all_friends(request, userid)),
            "fans": get_fans(userid),
        })
    else: # 没有user_id代表没有登录
        return login(request)

# 测试函数
def add_data_about_book(request):
    if request.method == "POST":
        if not models.Book.objects.filter(ISBN=request.POST['ISBN']).exists():
            ISBN = request.POST['ISBN']
            name = request.POST['name']
            author = request.POST['author']
            keyword = request.POST['keyword']
            des = request.POST['des']
            year = request.POST['year']
            pub = request.POST['pub']
            image = request.POST['image']
            star = float(request.POST['star'])
            book = models.Book(ISBN, name, author, keyword, des, year, pub, image, star)
            book.save()
            return render(request, "test.html")
    return render(request, "test.html")

