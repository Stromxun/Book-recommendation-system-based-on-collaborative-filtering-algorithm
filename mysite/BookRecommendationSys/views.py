import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import loader, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from . import models
# Create your views here.

def index(request):
    return render(request, 'index.html',)

def login(request):
    if request.method != 'POST':
        return render(request, "login.html")
    userID = request.POST['userID']
    password = request.POST['password']
    if not models.User.objects.filter(userID=userID).exists():
        return render(request, 'login.html', {'userID': -1})
    elif password == models.User.objects.all().get(userID=userID).pwd:
        request.session.set_expiry(1209600) # 两周
        request.session['userID'] = userID
        return HttpResponseRedirect('/{0}/home/'.format(userID))
    return render(request, "login.html", {'userID': int(userID)})

def generate_group(user): # 生成初始group
    group = models.Group(user=user, ups='[]')
    group.save()

def login_out(request):
    request.session.clear()
    return render(request, 'index.html')


def register_finished(request, user):
    return render(request, 'finish_regis.html', user)


def register(request):
    if request.method == "POST":
        # 生成用户个人信息
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        sign="你好，我是{0}，欢迎来到我的阅读空间".format(username) # 默认值
        sex="男" # 默认值
        path= "img/user_head/default.jpg"
        user = models.User(name=username, email=email, pwd=password, birthday=datetime.date(1975, 1, 1), sign=sign, sex=sex, avatar_path=path)
        user.save()
        # 生成好友群组
        generate_group(user)
        return register_finished(request, {'user' : user})
    return render(request, "register.html")



# 用户空间
def total_ding(request, user):
    forum_list = models.Forums.objects.filter(user=user)
    if not forum_list.exists():
        return 0
    ans = 0
    for forum in forum_list:
        ans = ans + forum.ding
    return ans


# 算是一种对数据库中存储字符串的解释
def get_id_list_from_str(group_list): # 输出字符串列表中的所有id
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

def all_friends(request, user): # 输出所有好友id
    ups = models.Group.objects.get(user=user).ups
    all_up = [] # 存储好友id
    for up_id in get_id_list_from_str(ups):
        all_up += (models.User.objects.filter(userID=up_id))
    return all_up

def add_up(request, goal_id):
    group = models.Group.objects.get(user=models.User.objects.get(userID=request.session['userID'])) # 找出
    group.ups = get_id_list_from_str(group.ups) + [goal_id]
    group.save()


def follow(request, goal_id): # session中的用户关注目标用户
    goal = models.User.objects.get(userID=goal_id)
    goal.fans += 1, goal.save() # 增加粉丝
    add_up(request, goal_id)


def up(request, goal_id):
    goal = models.User.objects.get(userID=goal_id)
    ups = []
    for up_id in get_id_list_from_str(models.Group.objects.get(user=goal).ups):
        ups += models.User.objects.get(userID=up_id)
    return render(request, 'up.html', {'goal': goal, 'ups' : ups})

def get_fans(userid):
    fans = models.User.objects.get(userID=userid).fans
    if fans < 1e6:
        return str(fans)
    elif fans < 1e9:
        return '{0}.{1}万'.format(int(fans/1e5), int(fans / 1e4) % 10)
    else: # 亿级单位
        return '{0}.{1}亿'.format(int(fans/1e9), int(fans / 1e8) % 10)

def home(request, goal_id):
    if goal_id :
        goal = models.User.objects.get(userID=goal_id)
        return render(request, "home.html", {
            "goal": goal,
            "ding": total_ding(request, goal_id),
            "num_friends": len(all_friends(request, goal_id)),
            "fans": get_fans(goal_id),
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

