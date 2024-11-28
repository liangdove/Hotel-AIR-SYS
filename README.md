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
