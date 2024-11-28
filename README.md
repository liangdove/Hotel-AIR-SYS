依赖：
py37 
django 2.2.13
matplotlib
numpy
pandas

运行：
rm db.sqlite3
python manage.py makemigrations 
python manage.py migrate
python manage.py runserver



检查出的问题：
1 计费费率不对，需要修改
2 有些js文件丢失
3 导出不了详单
4 5个房间同时访问不知道如何操作，setting中有 ALLOWED_HOSTS = ["*"]，猜测是开放了端口给外部请求使用
