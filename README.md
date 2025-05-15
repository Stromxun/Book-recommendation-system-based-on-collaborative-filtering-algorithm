# Book-recommendation-system-based-on-collaborative-filtering-algorithm

## 1、环境配置
### 后端
Python 3.10.11:https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe

Django:``` pip install django ```

MYSQL 8.0.40:https://dev.mysql.com/downloads/file/?id=536356

Pymsql: ``` pip install pymysql ```

mysqlclient ``` pip install mysqlclient ```
### 前端
HTML、CSS、JS

### IDE
Pycharm:https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=windows&code=PCC

## 2、配置Django后端

在mysite/mysite中的settings.py中有以下代码
```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sys',
        "USER": "root",
        "PASSWORD": "1234",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```
其中 
``ENGINE`` 表示本系统使用的数据库是MYSQL

``NAME`` 是使用的数据库库名

``USER`` 默认为root，具体是什么，看自己MYSQL配置

```PASSWORD``` 是自己设置的root密码

其他配置基本上不需要改变（具体看Django官方的配置数据库文档）

## 3、系统后端数据库迁移

通过在manage.py所在目录下使用以下两条指令进行数据库迁移，便可进行正常运行系统

```sh
python manage.py makemigrations
python manage.py migrate
```


## 4、初始化数据库

本系统使用的数据保存在dataset中，可以使用``navicat``导入.csv文件进行初始化图书数据

## 5、启动系统

通过Pycharm运行Django启动配置项可以启动系统。

在浏览器中输入网址 

``http://127.0.0.1:8000/index/`` 即可进入用户端

``http://127.0.0.1:8000/gly/`` 即可进入管理员端