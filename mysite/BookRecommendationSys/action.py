from .models import *

def revise(obj):
    if obj < 0:
        obj = 0


def init_recommend(request):
    ID = request.session.get('userID')
    books = Book.objects.all().order_by('score')[:50]  # 降序排列取前50
    favorites = []
    if ID and Favorites.objects.filter(user_id=ID).exists():
        favorites = get_id_list_from_str(Favorites.objects.get(user_id=ID).bookList)
    return [books, favorites]

def generate_group(user): # 生成初始group
    group = Group(user=user, ups='[]')
    group.save()

def generate_favorite(user):
    favorite = Favorites(user=user, bookList=[], isOpen=True, numOfBooks=0, listName='我的喜爱')
    favorite.save()

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

def add_up(request, goal_id):
    group = Group.objects.get(user=User.objects.get(userID=request.session['userID'])) # 找出
    group.ups = get_id_list_from_str(group.ups) + [goal_id]
    group.save()

def delete_up(request, goal_id):
    group = Group.objects.get(user=User.objects.get(userID=request.session['userID']))  # 找出
    new_ups = get_id_list_from_str(group.ups).remove(goal_id)
    if new_ups:
        group.ups = new_ups
    else:
        group.ups = '[]'
    group.save()

def add_like(request, ISBN):
    favorites = Favorites.objects.get(user=User.objects.get(userID=request.session['userID']))
    favorites.bookList = get_id_list_from_str(favorites.bookList) + [ISBN]
    favorites.numOfBooks += 1
    revise(favorites.numOfBooks)
    favorites.save()

def delete_like(request, ISBN):
    favorites = Favorites.objects.get(user=User.objects.get(userID=request.session['userID']))  # 找出
    new_book_list = get_id_list_from_str(favorites.bookList).remove(int(ISBN))
    if new_book_list:
        favorites.bookList = new_book_list
    else:
        favorites.bookList = '[]'
    favorites.numOfBooks -= 1
    revise(favorites.numOfBooks)
    favorites.save()

