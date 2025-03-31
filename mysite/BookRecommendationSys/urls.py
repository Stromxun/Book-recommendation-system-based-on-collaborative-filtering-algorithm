from django.urls import path

from . import views

urlpatterns = [
    # 主页
    path("index/", views.index, name="index"),
    path("login_out/", views.login_out, name="login_out"),

    # 书籍部分
    path("book/<str:ISBN>", views.book, name="book"),
    path("like/<str:ISBN>", views.like, name="like"),
    path("unlike/<str:ISBN>", views.unlike, name="unlike"),
    path("booklist/<int:bookListId>", views.booklist, name="booklist"),

    # 用户空间
    path("<int:goal_id>/home/", views.home, name="home"),
    path("<int:goal_id>/up/", views.up, name="up"),
    path("<int:goal_id>/follow/", views.follow, name="follow"),
    path("<int:goal_id>/unfollow/", views.unfollow, name="unfollow"),
    path("<int:goal_id>/booklist/", views.home_book_list, name="home_book_list"),

    # 登录部分
    path('login/', views.login, name='login'),

    # 注册部分
    path("register/", views.register, name="register"),
    path("register_finished/", views.register_finished, name="register_finished"),

    # 测试部分
    path("test/", views.add_data_about_book, name="test"),

]