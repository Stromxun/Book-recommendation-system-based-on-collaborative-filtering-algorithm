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
    path("booklist/<int:bookListId>/follow", views.booklist_follow, name="booklist_follow"),
    path("booklist/<int:bookListId>/unfollow", views.booklist_unfollow, name="booklist_unfollow"),
    path("booklist/<int:bookListId>/add_to_book_list", views.add_to_book_list, name="add_to_book_list"),
    path("booklist/<int:bookListId>/remove_from_book_list", views.remove_from_book_list, name="remove_from_book_list"),

    # 书论
    path("review/<str:ISBN>/write", views.review_write, name="review_write"),
    path("review/<int:review_id>/delete", views.review_delete, name="review_delete"),
    path("review/<int:review_id>/like", views.review_like, name="review_like"),
    path("review/<int:review_id>/unlike", views.review_unlike, name="review_unlike"),

    # 搜索
    path("search/", views.base_search, name="base_search"),
    path("search/<str:content>/", views.search, name="search"),

    # 增删书单
    path("booklist/create_bookList", views.create_bookList, name="create_bookList"),
    path("booklist/<int:bookListId>/delete_bookList", views.delete_bookList, name="delete_bookList"),
    path("booklist/<int:bookListId>/update_bookList", views.update_bookList, name="update_bookList"),

    # 用户空间
    path("<int:goal_id>/home/", views.home, name="home"),
    path("<int:goal_id>/up/", views.up, name="up"),
    path("<int:goal_id>/follow/", views.follow, name="follow"),
    path("<int:goal_id>/unfollow/", views.unfollow, name="unfollow"),
    path("<int:goal_id>/booklist/", views.home_book_list, name="home_book_list"),
    path("<int:goal_id>/setting/", views.home_setting, name="home_setting"),
    path("<int:goal_id>/forum/", views.home_forum, name="home_forum"),
    path("<int:goal_id>/forum/create/", views.forum_create, name="forum_create"),
    path("forum/<int:forum_id>/", views.forum, name="forum"),
    path("forum/<int:forum_id>/update/", views.forum_update, name="forum_update"),
    path("forum/<int:forum_id>/delete/", views.forum_delete, name="forum_delete"),
    path("forum/<int:forum_id>/like/", views.forum_like, name="forum_like"),
    path("forum/<int:forum_id>/unlike/", views.forum_unlike, name="forum_unlike"),
    path("forum/<int:forum_id>/write_comment/", views.forum_write_comment, name="forum_write_comment"),
    path("forum_comment/<int:comment_id>/delete_comment/", views.forum_delete_comment, name="forum_delete_comment"),
    path("comment/<int:comment_id>/like", views.comment_like, name="comment_like"),
    path("comment/<int:comment_id>/unlike", views.comment_unlike, name="comment_unlike"),

    # 反馈部分
    path("feedbacks/<int:userID>/", views.feedbacks, name="feedbacks"),
    path("feedbacks/<int:userID>/create/", views.feedback_create, name="feedback_create"),

    # 登录部分
    path('login/', views.login, name='login'),

    # 注册部分
    path("register/", views.register, name="register"),
    path("register_finished/", views.register_finished, name="register_finished"),

    # 测试部分
    path("test/", views.add_data_about_book, name="test"),

]