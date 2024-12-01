from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.sessions.models import Session

# 模拟的用户数据，实际使用时可以换成数据库存储
USER_DATA = {
    'ljl': '123456',
    'mjy': '123456',
    'dsx': '123456',
    'zyh': '123456',
    'jzy': '123456'
}

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 用户验证
        if USER_DATA.get(username) == password:
            # 登录成功，设置 session
            request.session['username'] = username
            return redirect('/')
        else:
            return HttpResponse('Invalid username or password', status=400)
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username in USER_DATA:
            return HttpResponse('Username already exists', status=400)
        
        # 注册成功，存储用户数据
        USER_DATA[username] = password
        return redirect('login')
    
    return render(request, 'register.html')


def logout_view(request):
    # 清除 session 中的用户名
    if 'username' in request.session:
        del request.session['username']
    return redirect('login')


# def home_view(request):
#     if 'username' in request.session:
#         username = request.session['username']
#         return HttpResponse(f'Hello, {username}')
#     return redirect('login')

