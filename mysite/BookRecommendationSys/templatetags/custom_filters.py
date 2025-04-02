from django import template
from ..action import *
register = template.Library()

@register.filter(name='to_int')
def to_int(value):
    try:
        # 移除 ISBN 中的非数字字符（如连字符）再转换
        cleaned = ''.join(c for c in value if c.isdigit())
        return int(cleaned)
    except (ValueError, TypeError):
        return 0  # 转换失败返回默认值

@register.filter(name='len_book_list')
def len_book_list(bookList):
    return len(get_id_list_from_str(bookList))

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg

@register.filter(name='get_n')
def get_n_img(bookList, n):
    books = get_id_list_from_str(bookList)[:n]
    return [Book.objects.get(ISBN=isbn).imageURL for isbn in books]

@register.filter(name='repeat')
def repeat(value, arg):
    return value * arg

@register.filter(name='get_books')
def get_books(bookList):
    bookIDs = get_id_list_from_str(bookList)
    books = []
    for id in bookIDs:
        books.append(Book.objects.get(ISBN=id))
    return books

@register.filter(name='generate_star')
def generate_star(score):
    star = ''
    for i in range(5):
        if score > 1.5:
            star += "1"
        elif 1.5 >= score >= 0.5:
            star += "2"
        else:
            star += "3"
        score -= 2
    return star

@register.filter(name='review_liked')
def review_liked(users, userID):
    userList = get_id_list_from_str(users)
    return to_int(userID) in userList