from .models import *

def revise(obj):
    return 0 if obj < 0 else obj


def init_recommend(request):
    ID = request.session.get('userID')
    books = Book.objects.all().order_by('-score')[:50]  # 降序排列取前50
    favorites = []
    if ID and Favorites.objects.filter(user_id=ID).exists():
        favorites = get_id_list_from_str(Favorites.objects.get(user_id=ID).bookList)
    return [books, favorites]

def generate_group(user): # 生成初始group
    group = Group(user=user, ups='[]')
    group.save()

def generate_favorite(user):
    favorite = Favorites(user=user, bookList='[]', isOpen=True, numOfBooks=0, listName='我的喜爱')
    favorite.save()

def generate_book_list_group(user):
    book_list_group = BookListGroup(user=user, book_list='[]')
    book_list_group.save()

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
    ups = Group.objects.get(user=user).ups
    all_up = [] # 存储好友id
    for up_id in get_id_list_from_str(ups):
        all_up += (User.objects.filter(userID=up_id))
    return all_up

def get_group(request):
    return Group.objects.get(user=User.objects.get(userID=request.session['userID']))

def add_up(request, goal_id):
    group = get_group(request)
    group.ups = get_id_list_from_str(group.ups) + [goal_id]
    group.save()

def delete_up(request, goal_id):
    group = get_group(request)
    new_ups = get_id_list_from_str(group.ups).remove(goal_id)
    if new_ups:
        group.ups = new_ups
    else:
        group.ups = '[]'
    group.save()

def get_favorite(request):
    return Favorites.objects.get(user=User.objects.get(userID=request.session['userID']))

def add_like(request, ISBN):
    favorites = get_favorite(request)
    favorites.bookList = get_id_list_from_str(favorites.bookList) + [ISBN]
    favorites.numOfBooks += 1
    favorites.numOfBooks = revise(favorites.numOfBooks)
    favorites.save()

def delete_like(request, ISBN):
    favorites = get_favorite(request)  # 找出
    new_book_list = get_id_list_from_str(favorites.bookList).remove(int(ISBN))
    if new_book_list:
        favorites.bookList = new_book_list
    else:
        favorites.bookList = '[]'
    favorites.numOfBooks -= 1
    favorites.numOfBooks = revise(favorites.numOfBooks)
    favorites.save()

def get_book_list_group(request):
    return BookListGroup.objects.get(user=User.objects.get(userID=request.session['userID']))

def add_book_list_follow(request, bookListId):
    book_list_group = get_book_list_group(request)
    book_list_group.book_list = get_id_list_from_str(book_list_group.book_list) + [bookListId]
    book_list = BookList.objects.get(bookListId=bookListId)
    book_list.fans += 1
    book_list.save()
    book_list_group.save()

def delete_book_list_follow(request, bookListId):
    book_list_group = get_book_list_group(request)  # 找出
    new_book_list = get_id_list_from_str(book_list_group.book_list).remove(int(bookListId))
    if new_book_list:
        book_list_group.book_list = new_book_list
    else:
        book_list_group.book_list = '[]'
    book_list = BookList.objects.get(bookListId=bookListId)
    book_list.fans -= 1
    book_list.fans = revise(book_list.fans)
    book_list.save()
    book_list_group.save()

def add_book_to_book_list(book_list_id, isbn):
    book_list = BookList.objects.get(bookListId=book_list_id)
    book_list.bookList = get_id_list_from_str(book_list.bookList) + [isbn]
    book_list.save()

def remove_book_in_list(book_list_id, isbn):
    book_list = BookList.objects.get(bookListId=book_list_id)
    new_book_list = get_id_list_from_str(book_list.bookList)
    new_book_list.remove(isbn)
    if new_book_list:
        book_list.bookList = new_book_list
    else:
        book_list.bookList = '[]'
    book_list.save()

# 书评
def re_like(request, review):
    user_list = get_id_list_from_str(review.zan_user)
    review.zan_user = user_list + [int(request.session['userID'])]
    review.zan += 1
    review.save()

def re_unlike(request, review):
    new_user_list = get_id_list_from_str(review.zan_user)
    new_user_list.remove(int(request.session['userID']))
    if new_user_list:
        review.zan_user = new_user_list
    else:
        review.zan_user = '[]'
    review.zan -= 1
    review.zan = revise(review.zan)
    review.save()

def forum_add_like(request, obj):
    obj.ding += 1
    obj.ding_user = get_id_list_from_str(obj.ding_user) + [int(request.session['userID'])]
    obj.save()

def forum_remove_like(request, obj):
    new_ding_user = get_id_list_from_str(obj.ding_user)
    new_ding_user.remove(int(request.session['userID']))
    if new_ding_user:
        obj.ding_user = new_ding_user
    else:
        obj.ding_user = '[]'
    obj.ding -= 1
    obj.ding = revise(obj.ding)
    obj.save()