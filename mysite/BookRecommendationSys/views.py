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

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        if not models.User.objects.filter(name=username).exists():
            email = request.POST['email']
            password = request.POST['password']
            sign="你好，我是{0}，欢迎来到我的阅读空间".format(username) # 默认值
            sex="男" # 默认值
            path= "img/user_head/default.jpg"
            user = models.User(name=username, email=email, pwd=password, birthday=datetime.date(1975, 1, 1), sign=sign, sex=sex, avatar_path=path)
            user.save()
            return render(request, "index.html")
    return render(request, "register.html")

# 系统功能主页
def Book(request):
    return render(request)

# 用户空间
def user_home(request, userid):
    if userid :
        user = models.User.objects.get(userID=userid)
        return render(request, "home.html", {"user": user})
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

