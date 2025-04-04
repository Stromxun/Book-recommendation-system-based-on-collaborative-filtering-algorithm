import datetime
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
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
        path= "img/user_head/default0.jpg"
        user = User(name=username, email=email, pwd=password, birthday=datetime.date(1975, 1, 1), sign=sign, sex=sex, avatar_path=path)
        user.save()
        # 生成好友群组
        generate_group(user)
        generate_favorite(user)
        generate_book_list_group(user)
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
    user = User.objects.get(userID=request.session.get('userID'))
    booklist_group = BookListGroup.objects.get(user=user)
    group = get_id_list_from_str(booklist_group.book_list)
    return render(request, 'booklist.html', {'booklist': bookList, 'is_following' : (int(bookListId) in group)})


def add_to_book_list(request, bookListId):
    booklist = get_object_or_404(BookList, bookListId=bookListId)
    userID = request.session.get('userID')

    if int(userID) != booklist.user.userID:
        return JsonResponse({'status': 'error', 'message': '无操作权限'}, status=403)

    isbn = int(request.POST.get('isbn'))
    if not Book.objects.filter(ISBN=isbn).exists():
        messages.error(request, '查询不到此书')
        return redirect('booklist', bookListId=bookListId)
    add_book_to_book_list(bookListId, isbn)
    return redirect('booklist', bookListId=bookListId)


def remove_from_book_list(request, bookListId):
    book_list = get_object_or_404(BookList, bookListId=bookListId)

    if int(request.session.get('userID')) != book_list.user.userID:
        return JsonResponse({'status': 'error', 'message': '无操作权限'}, status=403)

    isbn = int(request.POST.get('isbn'))
    remove_book_in_list(bookListId, isbn)
    return redirect('booklist', bookListId=bookListId)


def booklist_follow(request, bookListId):
    add_book_list_follow(request, bookListId)
    return HttpResponseRedirect('/booklist/{0}'.format(bookListId))

def booklist_unfollow(request, bookListId):
    delete_book_list_follow(request, bookListId)
    return HttpResponseRedirect('/booklist/{0}'.format(bookListId))

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
    # 获取目标用户
    user = get_object_or_404(User, userID=goal_id)

    # 获取当前请求类型参数
    list_type = request.GET.get('type', 'my')

    # 初始化查询集
    my_book_list = BookList.objects.filter(user=user)
    follow_book_lists = BookList.objects.none()

    try:
        # 处理可能不存在的关注组
        follow_group = BookListGroup.objects.get(user=user).book_list
        list_ids = get_id_list_from_str(follow_group)

        # 优化查询：使用Q对象组合条件
        follow_book_lists = BookList.objects.filter(
            Q(bookListId__in=list_ids)
        ).select_related('user')

    except BookListGroup.DoesNotExist:
        pass

    # 根据类型选择数据
    if list_type == 'follow':
        book_lists = follow_book_lists
    else:  # 默认显示我的书单
        book_lists = my_book_list

    # 统计数量（使用缓存避免重复查询）
    context = {
        'goal': user,
        'book_lists': book_lists,
        'list_type': list_type,
        'my_count': my_book_list.count(),
        'follow_count': follow_book_lists.count(),
    }

    return render(request, 'home_booklist.html', context)

def create_bookList(request):
    user = User.objects.get(userID=request.session.get('userID'))
    # 创建一个默认模板书单
    booklist = BookList(bookListTitle='我的书单', user=user, description='这是我创建的书单！', bookList='[]')
    booklist.save()
    return HttpResponseRedirect('/{0}/booklist'.format(user.userID))



def delete_bookList(request, bookListId):
    return None

def update_bookList(request, bookListId):
    booklist = BookList.objects.get(bookListId=bookListId)
    if request.method == 'POST':
        booklist.bookListTitle = request.POST.get('title')
        booklist.description = request.POST.get('description')
        booklist.is_public =  request.POST.get('privacy') == 'public'
        booklist.save()
        return HttpResponseRedirect('/{0}/booklist'.format(booklist.user.userID))
    return render(request, 'booklist_update.html', {'booklist': booklist})

def home_setting(request, goal_id):
    user = User.objects.get(userID=goal_id)
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.sex = '男' if request.POST.get('sex') == '男' else '女'
        user.avatar_path = "img/user_head/default0.jpg" if user.sex == '男' else "img/user_head/default1.png"
        user.birthday = request.POST.get('birthday')
        user.sign = request.POST.get('sign')
        pass_word = request.POST.get('password')
        if pass_word:
            user.password = pass_word
        user.save()
        return HttpResponseRedirect('/{0}/home'.format(user.userID))
    return render(request, 'home_setting.html', {'user':user})


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


