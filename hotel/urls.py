"""hotel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from Air_Condition.views import *
from Air_Condition.customer import login_view, register_view,logout_view
# 对应的网页及操作
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', tst),
    path('', client_off), # 修改
    path('on/', client_on),
    
    # 注册与登录
    path('login', login_view),
    path('register/',register_view),
    path('logout', logout_view),

    # 测试
    path('get/', get),
    re_path(r'der-post$', post),

    # 客户端按钮(操作)
    path('power/', power),
    path('high/', change_high),
    path('mid/', change_mid),
    path('low/', change_low),
    path('up/', change_up),
    path('down/', change_down),

    # 空调管理员
    path('init/', init),
    path('init_submit/', init_submit),
    path('monitor/', monitor),

    # 前台
    path('recp/', reception_init),
    path('recp_submit/', reception),

    # 经理
    path('manager/', manager),
    path('manager_month/', manager_month),
    path('manager_week/', manager_week),
]