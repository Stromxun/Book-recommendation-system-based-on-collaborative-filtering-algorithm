from django.urls import path

from . import views

urlpatterns = [
    # 主页
    path("index/", views.index, {'userid': ''}, name="index"),

    # 用户空间
    path("<int:userid>/home/", views.user_home, name="home"),

    # 登录部分
    path('login/', views.login, name='login'),

    # 注册部分
    path("register/", views.register, name="register"),


    # 测试部分
    path("test/", views.add_data_about_book, name="test"),

]