import datetime
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .action import *
from .models import *


def index(request): # 优化处
    # 获取所有书籍并按id排序
    book_list, favorites = init_recommend(request)
    # 每页显示50本
    paginator = Paginator(book_list, 50)
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)
    return render(request, 'index.html', {'books': books, 'favorites': favorites})

def login(request):
    if request.method != 'POST' or not request.POST.get('userID'):
        return render(request, "login.html")
    userID = request.POST.get('userID')
    password = request.POST.get('password')
    if not User.objects.filter(userID=userID).exists():
        return render(request, 'login.html', {'userID': -1})
    elif password == User.objects.all().get(userID=userID).pwd:
        request.session.set_expiry(1209600) # 两周
        request.session['userID'] = userID
        return HttpResponseRedirect('/{0}/home/'.format(userID))
    return render(request, "login.html", {'userID': int(userID)})



def login_out(request):
    request.session.clear()
    return index(request)


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
        user = User(name=username, email=email, pwd=password, birthday=datetime.date(1975, 1, 1), sign=sign, sex=sex, avatar_path=path)
        user.save()
        # 生成好友群组
        generate_group(user)
        generate_favorite(user)
        return register_finished(request, {'user' : user})
    return render(request, "register.html")

def book(request, ISBN):
    book = Book.objects.all().get(ISBN=ISBN)
    # 预处理星级数据
    full_score = 10  # 满分10分
    max_stars = 5  # 最大5星
    star_value = full_score / max_stars  # 每星代表2分

    # 评分
    stars = []
    remaining_score = book.score
    for _ in range(max_stars):
        if remaining_score >= star_value * 0.75:  # 1.5分以上显示全星
            stars.append(1)
            remaining_score -= star_value
        elif remaining_score >= star_value * 0.25:  # 0.5分以上显示半星
            stars.append(0.5)
            remaining_score = max(remaining_score - star_value, 0)
        else:
            stars.append(0)

    userID = request.session.get('userID')
    if not userID:
        return render(request, "book.html", {'book': book, 'stars': stars})
    user = User.objects.get(userID=userID)

    my_favorite = get_id_list_from_str(Favorites.objects.get(user=user).bookList)
    is_liked = (int(ISBN) in my_favorite)
    return render(request, "book.html", {'book': book, 'stars': stars, 'is_liked': is_liked})

def booklist(request, bookListId):
    bookList = BookList.objects.get(bookListId=bookListId)
    return render(request, 'booklist.html', {'booklist': bookList})

def like(request, ISBN):
    add_like(request, ISBN)
    return HttpResponseRedirect('/book/{0}'.format(ISBN))

def unlike(request, ISBN):
    delete_like(request, ISBN)
    return HttpResponseRedirect('/book/{0}'.format(ISBN))
# 用户空间

def is_followed(request, goal_id):
    group = Group.objects.get(user=User.objects.get(userID=request.session['userID']))  # 找出
    return goal_id in get_id_list_from_str(group.ups)

def follow(request, goal_id): # session中的用户关注目标用户
    goal = User.objects.get(userID=goal_id)
    goal.fans += 1
    goal.save() # 增加粉丝
    add_up(request, goal_id)
    return HttpResponseRedirect('/{0}/home/'.format(goal_id), {'followed' : is_followed(request, goal_id)})

def unfollow(request, goal_id): # 取消关注
    goal = User.objects.get(userID=goal_id)
    goal.fans -= 1
    if goal.fans < 0:
        goal.fans = 0
    goal.save()  # 减少粉丝
    delete_up(request, goal_id)
    return HttpResponseRedirect('/{0}/home/'.format(goal_id), {'followed': is_followed(request, goal_id)})

def up(request, goal_id):
    goal = User.objects.get(userID=goal_id)
    ups = []
    for up_id in get_id_list_from_str(Group.objects.get(user=goal).ups):
        ups += [User.objects.get(userID=up_id)]
    return render(request, 'up.html', {'goal': goal, 'ups' : ups})

def get_fans(userid):
    fans = User.objects.get(userID=userid).fans
    if fans < 1e6:
        return str(fans)
    elif fans < 1e9:
        return '{0}.{1}万'.format(int(fans/1e5), int(fans / 1e4) % 10)
    else: # 亿级单位
        return '{0}.{1}亿'.format(int(fans/1e9), int(fans / 1e8) % 10)

def home(request, goal_id):
    if goal_id :
        goal = User.objects.get(userID=goal_id)
        return render(request, "home.html", {
            "goal": goal,
            "ding": goal.ding,
            "num_friends": len(all_friends(request, goal_id)),
            "fans": get_fans(goal_id),
            "followed": is_followed(request, goal_id)
        })
    else: # 没有user_id代表没有登录
        return login(request)

def home_book_list(request, goal_id):
    user = User.objects.get(userID=goal_id)
    my_book_list = BookList.objects.filter(user=user)
    return render(request, 'home_booklist.html', {'goal': user, 'book_lists' : my_book_list})


# 测试函数
def add_data_about_book(request):
    if request.method == "POST":
        if not Book.objects.filter(ISBN=request.POST['ISBN']).exists():
            ISBN = request.POST['ISBN']
            name = request.POST['name']
            author = request.POST['author']
            keyword = request.POST['keyword']
            des = request.POST['des']
            year = request.POST['year']
            pub = request.POST['pub']
            image = request.POST['image']
            star = float(request.POST['star'])
            book = Book(ISBN, name, author, keyword, des, year, pub, image, star)
            book.save()
            return render(request, "test.html")
    return render(request, "test.html")



    return None