import datetime
from django.contrib import messages
from django.db.models import Q, Case, When
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import urlencode
from django.db.models import F, Value, FloatField
from django.db.models.functions import Greatest

from .action import *
from .models import *
from .recommend import *


def index(request): # 优化处
    # 获取所有书籍并按id排序
    book_list, favorites = [], []
    ID = request.session.get('ID')
    if request.session.get('userID'):
        book_list = generate_recommend(request.session.get('userID'))
    else:
        book_list = init_recommend()
    if ID and Favorites.objects.filter(user_id=ID).exists():
        favorites = get_id_list_from_str(Favorites.objects.get(user_id=ID).bookList)
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
        if not Token.objects.get(user=userID).tokenLogin:
            return render(request, 'login.html', {'userID': -2})
        request.session.set_expiry(1209600) # 两周
        request.session['userID'] = userID
        return HttpResponseRedirect('/index/')
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
        generate_user_history(user)
        generate_token(user)
        return register_finished(request, {'user' : user})
    return render(request, "register.html")

def book(request, ISBN):
    book = Book.objects.all().get(ISBN=ISBN)
    userID = None
    if request.session.get('userID'):
        userID = request.session.get('userID')
        update_book_history(userID, ISBN)
    # 书评
    top_reviews = Review.objects.filter(book=book).order_by('-star')
    if not userID:
        return render(request, "book.html", {'book': book, 'top_reviews': top_reviews})
    user = User.objects.get(userID=userID)

    my_favorite = get_id_list_from_str(Favorites.objects.get(user=user).bookList)
    is_liked = (int(ISBN) in my_favorite)

    return render(request, "book.html", {'book': book, 'is_liked': is_liked, 'top_reviews': top_reviews})

def review_write(request, ISBN):
    book = Book.objects.all().get(ISBN=ISBN)
    if request.method == "POST":
        content = request.POST['comment']
        user = User.objects.get(userID=request.session.get('userID'))
        star = request.POST['star']
        new_review = Review(content=content, user=user, star=star, book=book)
        new_review.save()
        return HttpResponseRedirect('/book/{0}'.format(ISBN))
    return render(request, 'comment_write.html', {'book': book})

def review_like(request, review_id): # 输入评论id
    review = Review.objects.get(pk=review_id)
    re_like(request, review)
    return HttpResponseRedirect('/book/{0}'.format(review.book.ISBN))


def review_unlike(request, review_id):
    review = Review.objects.get(pk=review_id)
    re_unlike(request, review)
    return HttpResponseRedirect('/book/{0}'.format(review.book.ISBN))

def review_delete(request, review_id):
    review = Review.objects.get(pk=review_id)
    ISBN = review.book.ISBN
    review.delete()
    return HttpResponseRedirect('/book/{0}'.format(ISBN))

def booklist(request, bookListId):
    bookList = BookList.objects.get(bookListId=bookListId)
    user = User.objects.get(userID=request.session.get('userID'))
    booklist_group = FollowBookListGroup.objects.get(user=user)
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
        follow_group = FollowBookListGroup.objects.get(user=user).book_list
        list_ids = get_id_list_from_str(follow_group)

        # 优化查询：使用Q对象组合条件
        follow_book_lists = BookList.objects.filter(
            Q(bookListId__in=list_ids)
        ).select_related('user')

    except FollowBookListGroup.DoesNotExist:
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
    booklist = BookList.objects.get(bookListId=bookListId)
    userID = booklist.user.userID
    booklist.delete()
    return HttpResponseRedirect('/{0}/booklist'.format(userID))

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


def base_search(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        return HttpResponseRedirect('/search/{0}?type=book'.format(content))
    return HttpResponseRedirect('/index')


def search(request, content): # 搜索
    search_type = request.GET.get('type', 'book')
    page = request.GET.get('page', 1)

    context = {
        'content': content,
        'type': search_type
    }

    # 设置分页配置
    pagination_config = {
        'book': {'per_page': 50, 'context_key': 'books'},
        'booklist': {'per_page': 50, 'context_key': 'booklists'},
        'user': {'per_page': 150, 'context_key': 'users'}
    }

    try:
        config = pagination_config[search_type]
        per_page = config['per_page']
        context_key = config['context_key']
    except KeyError:
        search_type = 'book'
        config = pagination_config['book']
        per_page = config['per_page']
        context_key = config['context_key']

    # 查询逻辑
    if search_type == 'book':
        query = (
                Q(BookTitle__icontains=content) |
                Q(description__icontains=content)
        )
        if request.session.get('userID'):
            update_search_history(request.session.get('userID'), content)
        try:
            query |= Q(ISBN=int(content))
        except ValueError:
            pass
        results = Book.objects.filter(query).order_by('score').annotate(
            # 计算匹配相关度（示例算法）
            relevance=Greatest(
                # 标题匹配权重0.8
                Case(
                    When(BookTitle__icontains=content, then=Value(0.8)),
                    default=Value(0.0),
                    output_field=FloatField()
                ),
                # 描述匹配权重0.5
                Case(
                    When(description__icontains=content, then=Value(0.5)),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
        ).order_by(
            '-score',  # 第一排序条件：评分降序
            '-relevance'  # 第二排序条件：相关度降序
        )

    elif search_type == 'booklist':
        query = Q(bookListTitle__icontains=content) | Q(description__icontains=content)
        try:
            query |= Q(bookListId=int(content))
        except ValueError:
            pass
        results = BookList.objects.filter(query).annotate(
            # 计算匹配相关度（示例算法）
            relevance=Greatest(
                # 标题匹配权重0.8
                Case(
                    When(bookListTitle__icontains=content, then=Value(0.8)),
                    default=Value(0.0),
                    output_field=FloatField()
                ),
                # 描述匹配权重0.5
                Case(
                    When(description__icontains=content, then=Value(0.5)),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
        ).order_by(
            '-fans',  # 第一排序条件：评分降序
            '-relevance'  # 第二排序条件：相关度降序
        )

    else:  # user
        query = Q(name__icontains=content)
        try:
            query |= Q(userID=int(content))
        except ValueError:
            pass
        results = User.objects.filter(query).order_by('userID')

    # 分页处理
    paginator = Paginator(results, per_page)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context.update({
        context_key: page_obj,
        'count': paginator.count,
        'page_obj': page_obj
    })

    return render(request, 'search.html', context)

def forum(request, forum_id): # 帖子
    f = Forum.objects.get(id=forum_id)
    comments = Comment.objects.filter(forum=f).order_by('-ding')
    return render(request, 'forum.html', {'post': f, 'reviews': comments})


def home_forum(request, goal_id):
    goal = User.objects.get(userID=goal_id)
    forums = Forum.objects.filter(user=goal).order_by('-addTime')
    return render(request, 'home_forum.html', {'goal': goal, 'forums': forums})


def forum_create(request, goal_id):
    user = User.objects.get(userID=goal_id)
    if request.method == "POST":
        title = request.POST['title']
        content = request.POST['content']
        privacy = request.POST['privacy'] == "public"
        forum = Forum(user=user, title=title, content=content, is_public=privacy)
        forum.save()
        return HttpResponseRedirect('/{0}/forum'.format(user.userID))
    return render(request, 'forum_write.html', {'goal':user})


def forum_update(request, forum_id):
    forum = Forum.objects.get(id=forum_id)
    if request.method == "POST":
        forum.title = request.POST['title']
        forum.content = request.POST['content']
        forum.is_public = (request.POST['privacy'] == "public")
        forum.save()
        return HttpResponseRedirect('/{0}/forum'.format(forum.user.userID))
    return render(request, 'forum_update.html', {'forum':forum})


def forum_delete(request, forum_id):
    forum = Forum.objects.get(id=forum_id)
    userID = forum.user.userID
    forum.delete()
    return HttpResponseRedirect('/{0}/forum'.format(userID))


def forum_write_comment(request, forum_id):
    forum = Forum.objects.get(id=forum_id)
    if request.method == "POST":
        content = request.POST['comment']
        user = User.objects.get(userID=int(request.session['userID']))
        comment = Comment(forum=forum, content=content,user=user)
        forum.numComm += 1
        comment.save()
        forum.save()
        return HttpResponseRedirect('/forum/{0}'.format(forum.id))
    return render(request, 'forum_comment_write.html', {'post': forum})

def forum_delete_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    forum = Forum.objects.get(id=comment.forum.id)
    comment.delete()
    forum.numComm -= 1
    forum.save()
    return HttpResponseRedirect('/forum/{0}'.format(forum.id))


def forum_like(request, forum_id):
    forum_add_like(request, Forum.objects.get(id=forum_id))
    return HttpResponseRedirect('/forum/{0}'.format(forum_id))


def forum_unlike(request, forum_id):
    forum_remove_like(request, Forum.objects.get(id=forum_id))
    return HttpResponseRedirect('/forum/{0}'.format(forum_id))


def comment_like(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    forum_add_like(request, comment)
    return HttpResponseRedirect('/forum/{0}'.format(comment.forum.id))


def comment_unlike(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    forum_remove_like(request, comment)
    return HttpResponseRedirect('/forum/{0}'.format(comment.forum.id))


def feedbacks(request, userID):
    user = User.objects.get(userID=userID)
    feedbacks = Feedback.objects.filter(user=user).order_by('checkStatus').order_by('-addTime')
    return render(request, 'feedbacks.html', {'feedbacks':feedbacks, 'user':user})


def feedback_create(request, userID):
    user = User.objects.get(userID=userID)
    if request.method == "POST":
        title = request.POST['title']
        description = request.POST['content']
        feedback = Feedback(user=user, title=title, description=description)
        feedback.save()
        return HttpResponseRedirect('/feedbacks/{0}/'.format(user.userID))
    return render(request, 'feedback_create.html', {'goal':user})


def admin_login(request):
    if request.method != 'POST' or not request.POST.get('userID'):
        return render(request, "admin_login.html")
    adminID = request.POST.get('userID')
    password = request.POST.get('password')
    if not Admin.objects.filter(pk=adminID).exists():
        return render(request, 'admin_login.html', {'userID': -1})
    elif password == Admin.objects.all().get(pk=adminID).pwd:
        request.session.set_expiry(1209600) # 两周
        request.session['adminID'] = adminID
        return HttpResponseRedirect('/gly/{0}/manage'.format(adminID))
    return render(request, "admin_login.html", {'userID': int(adminID)})

def manage(request, adminID):
    # 书籍管理
    book_list = Book.objects.all().order_by('ISBN')
    paginator = Paginator(book_list, 50)
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)

    # 用户管理
    users = User.objects.all()

    # 反馈管理
    feedbacks = Feedback.objects.all().order_by('checkStatus')

    context = {
        'adminID': adminID,
        'books': books,
        'users': users,
        'feedbacks': feedbacks,
    }
    return render(request, 'admin_manage.html', context)

def admin_login_out(request):
    request.session.clear()
    return HttpResponseRedirect('/gly/')

def book_create(request):
    if request.method == "POST":
        if not Book.objects.filter(ISBN=request.POST['ISBN']).exists():
            ISBN = request.POST['ISBN']
            name = request.POST['name']
            author = request.POST['author']
            keyword = request.POST['keyword']
            des = request.POST['description']
            year = request.POST['year']
            pub = request.POST['pub']
            image = request.POST['image']
            star = float(request.POST['star'])
            book = Book(ISBN, name, author, keyword, des, year, pub, image, star)
            book.save()
            return HttpResponseRedirect('/gly/{0}/manage/'.format(request.session['adminID']))
    return render(request, "admin_book_create.html")

def book_delete(request, ISBN):
    book = Book.objects.get(ISBN=ISBN)
    book.delete()
    return HttpResponseRedirect('/gly/{0}/manage/'.format(request.session['adminID']))


def book_edit(request, ISBN):
    book = Book.objects.get(ISBN=ISBN)
    if request.method == "POST":
        book.ISBN = request.POST['ISBN']
        book.BookTitle = request.POST['name']
        book.BookAuthor = request.POST['author']
        book.keyword = request.POST['keyword']
        book.description = request.POST['description']
        book.YearOfPublication = request.POST['year']
        book.Publisher = request.POST['pub']
        book.imageURL = request.POST['image']
        book.score = float(request.POST['star'])
        book.save()
        return HttpResponseRedirect('/gly/{0}/manage/'.format(request.session['adminID']))
    return render(request, "admin_book_update.html", {'book': book})


def update_user_status(request, userID, utype):
    admin = Admin.objects.get(pk=request.session['adminID'])
    # 如果没有token，创建一个新token
    user = User.objects.get(pk=userID)
    if not Token.objects.filter(user=user).exists():
        token = Token(user=user)
        token.save()

    token = Token.objects.get(user=user)
    if utype == 'comment':
        token.tokenComment = not token.tokenComment
    elif utype == 'public':
        token.tokenPublic = not token.tokenPublic
    elif utype == 'login':
        token.tokenLogin = not token.tokenLogin
    token.save()
    base_url = f'/gly/{admin.id}/manage/'
    query_params = {'q': '', 'section': 'user-permission'}
    return HttpResponseRedirect(f"{base_url}?{urlencode(query_params)}")


def deal_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)

    if request.method == 'POST':
        # 验证管理员权限
        if 'adminID' not in request.session:
            return redirect('admin_login')

        # 处理表单数据
        feedback.replyInformation = request.POST.get('reply')
        feedback.checkStatus = 'resolve_status' in request.POST
        feedback.admin_id = request.session['adminID']
        feedback.replyTime = timezone.now()
        feedback.save()

        return HttpResponseRedirect('/gly/{0}/manage/'.format(request.session['adminID']))

    return render(request, 'admin_feedback.html', {'feedback': feedback})