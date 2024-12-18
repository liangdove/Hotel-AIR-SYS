from django.db import models
from django.utils import timezone
import threading
import django
from django.http import HttpResponse
import csv
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from django.db.models import Q
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 下面这个网站提供了详细的字段类型参考，请大家仔细比较，选择最优字段类型。
# note: https://docs.djangoproject.com/zh-hans/2.2/ref/models/fields/#field-types


class ServingQueue(models.Model):
    """
    正在服务的队列，存放所有正在服务的房间对象
    """
    # 在调度队列中的房间对象
    # 注：不确定这么写好不好，我觉得serve_time应该和房间对象绑定在一起可能会好一点。
    # 如果有更好的类型，请替换。
    room_list = []
    cishu=0
    serving_num = models.IntegerField(verbose_name='服务对象数', default=0)

    def __init__(self):
        super().__init__()
        self.serving_num = 0

    def insert(self, room):
        room.state = 1
        room.scheduling_num += 1
        self.room_list.append(room)
        self.room_list.sort(key=lambda x: (x.fan_speed))  # 按照风速排序,服务队列中风速优先
        self.serving_num += 1
        return True

    #  修改温度
    def set_target_temp(self, room_id, target_temp):
        for room in self.room_list:
            if room.room_id == room_id:
                room.target_temp = target_temp
                break
        return True

    #  修改风速
    def set_fan_speed(self, room_id, fan_speed, fee_rate):
        for room in self.room_list:
            if room.room_id == room_id:
                room.fan_speed = fan_speed
                room.fee_rate = fee_rate
                self.room_list.sort(key=lambda x: (x.fan_speed))  # 按照风速排序,服务队列中风速优先
                break
        return True

    def delete_room(self, room):
        """
        从调度队列删除对应的房间
        :param room:
        :return:
        """
        self.room_list.remove(room)
        self.serving_num -= 1
        return True

    def update_serve_time(self,rooms):
        if self.serving_num != 0:
            for room in self.room_list:
                room.serve_time += 1
        #print(rooms[0])
        print(f"第{self.cishu}次打印：")
        self.cishu=self.cishu+1
        for record in range(len(rooms)):
    
            if rooms[record]:
                for i in range(0,5):
                  if rooms[record].room_id == i:
                    
                    print(f"队列： 房间号：{rooms[record].room_id},运行状态：{rooms[record].state}, 当前温度：{rooms[record].current_temp}, 目标温度：{rooms[record].target_temp}, 风速：{rooms[record].fan_speed}, 费用：{rooms[record].fee}")        
        
                  

        timer = threading.Timer(60/6, lambda: self.update_serve_time(rooms))  # 每1min执行一次函数
        timer.start()

    def auto_fee_temp(self, mode):
        """
        1元/度；
        回温和计费函数，设定风速H:1元/min,即0.016元/s,
        M:0.5元/min,即0.008元/s,
        L:0.3333元/min,即0.005元/s,
        mode=1,制热
        mode=2,制冷
        :return:
        """
        if mode == 1:
            for room in self.room_list:
                if room.fan_speed == 1:
                    room.fee += 0.016
                    room.current_temp += 0.016
                elif room.fan_speed == 2:
                    room.fee += 0.008
                    room.current_temp += 0.008
                else:
                    room.fee += 0.005
                    room.current_temp += 0.005
            timer = threading.Timer(1/6, self.auto_fee_temp, [1])  # 每1秒执行一次函数
            timer.start()
        else:
            for room in self.room_list:
                if room.fan_speed == 1:
                    room.fee += 0.016
                    room.current_temp -= 0.03
                elif room.fan_speed == 2:
                    room.fee += 0.008
                    room.current_temp -= 0.025
                else:
                    room.fee += 0.005
                    room.current_temp -= 0.016
            timer = threading.Timer(1/6, self.auto_fee_temp, [2])  # 每1秒执行一次函数
            timer.start()


class WaitingQueue(models.Model):
    """
    等待队列，存放所有等待服务的房间对象
    """
    room_list = []
    
    waiting_num = models.IntegerField(verbose_name='等待对象数', default=0)

    def __init__(self):
        super().__init__()
        self.waiting_num = 0

    def set_target_temp(self, room_id, target_temp):
        for room in self.room_list:
            if room.room_id == room_id:
                room.target_temp = target_temp
                break
        return True

    def set_fan_speed(self, room_id, fan_speed, fee_rate):
        for room in self.room_list:
            if room.room_id == room_id:
                room.fan_speed = fan_speed
                room.fee_rate = fee_rate
                break
        return True

    def delete_room(self, room):
        """
        从等待队列删除对应的房间
        :param room:
        :return:
        """
        self.room_list.remove(room)
        self.waiting_num -= 1
        return True

    #   参数用room对象更好，
    def insert(self, room):
        room.state = 2
        room.scheduling_num += 1
        self.room_list.append(room)
        self.waiting_num += 1
        return True

    def update_wait_time(self):
        if self.waiting_num != 0:
            for room in self.room_list:
                room.wait_time += 1
        
        # for record in range(len(self.room_list)):
    
        #     if self.room_list[record]:
        #         for i in range(0,5):
        #           if self.room_list[record].room_id == i:
                    
                    # print(f"Waiting队列： 房间号：{self.room_list[record].room_id}, 当前温度：{self.room_list[record].current_temp}, 目标温度：{self.room_list[record].target_temp}, 风速：{self.room_list[record].fan_speed}, 费用：{self.room_list[record].fee}")        
        timer = threading.Timer(60/6, self.update_wait_time)  # 每1min执行一次函数
        timer.start()


class Scheduler(models.Model):
    """
    名称：调度器、调度对象、中控机
    作用：作为温控系统的中心，为到来的请求分配服务对象，提供计费功能
    """

    STATE_CHOICE = [
        (1, 'WORKING'),
        (2, 'SHUTDOWN'),
        (3, 'SETMODE'),
        (4, 'READY')
    ]

    TEMP_CHOICE = [
        (22, "制热"),
        (25, "制冷")
    ]
    # 第一次发出开机请求的房间数
    request_num = 0

    # 房间请求数，详单中的主键
    request_id = 0

    # 中控机所处的状态
    state = models.IntegerField(verbose_name='中控机状态', choices=STATE_CHOICE, default=2)

    # 最高温度限制
    temp_high_limit = models.IntegerField(verbose_name='最高温度限制', default=0)

    # 最低温度限制
    temp_low_limit = models.IntegerField(verbose_name="最低温度限制", default=0)

    # 默认目标温度
    default_target_temp = models.IntegerField(verbose_name="默认目标温度", choices=TEMP_CHOICE, default=25)

    # 高风速时的费率
    fee_rate_h = models.FloatField(verbose_name="高风速费率", default=1.0)

    # 低风速时的费率
    fee_rate_l = models.FloatField(verbose_name="低风速费率", default=0.3333)

    # 中风速时的费率
    fee_rate_m = models.FloatField(verbose_name="中风速费率", default=0.5)

    #  等待队列
    WQ = WaitingQueue()

    #  服务队列
    SQ = ServingQueue()

    #  存储5个房间,房间开始时的状态都是3--“SHUTDOWN”关机状态
    rooms = []

    def power_on(self):
        """
        开启中控机，中控机状态修改为”SETMODE“
        初始化房间队列
        :return:
        """
        Room.objects.all().delete()
        self.state = 3
        #  只要服务队列有房间就计费和计温,制热mode=1,制冷mode=2,
        if self.default_target_temp == 22:
            self.SQ.auto_fee_temp(1)
        else:
            self.SQ.auto_fee_temp(2)

        # 开启调度函数
        self.scheduling()
        #  只要有服务就检查是否有房间达到目标温度
        self.check_target_arrive()
        # 开启调度队列和等待队列的计时功能
        self.SQ.update_serve_time(self.rooms)
        self.WQ.update_wait_time()

        return self.state

    def set_init_temp(self, room_id, init_temp):
        """
        设置房间的初始温度
        :param room_id:
        :param init_temp:
        :return:
        """
        for room in self.rooms:
            if room.room_id == room_id:
                room.init_temp = init_temp

    def request_on(self, room_id, current_room_temp):
        """
        一个请求到来，第一次开机分配房间对象然后处理，否则直接处理
        调用调度算法
        问题：房间ID如何分配的
        开始计费和计温
        :param room_id:
        :param current_room_temp:
        :return:
        """
        return_room = Room(request_id=self.request_id) #调用Room类，生成对象
        flag = 1
        for room in self.rooms:
            if room.room_id == room_id:  # 不是第一次开机，直接处理
                room.current_temp = current_room_temp
                flag = 0
                if self.SQ.serving_num < 3:  # 服务队列未满
                    self.SQ.insert(room)
                else:  # 服务队列已满
                    self.WQ.insert(room)

                return_room = room
                #  写入数据库
                room.request_time = timezone.now()
                room.request_id = self.request_id
                self.request_id += 1
                room.operation = 3
                room.save(force_insert=True)
        if flag == 1:  # 是第一次开机，先分配房间对象再处理
            temp_room = return_room
            self.request_num += 1  # 发出第一次开机请求的房间数加一
            if self.request_num > 5:  # 控制只能有五个房间开机
                return False  # 返回

            temp_room.room_id = room_id
            temp_room.current_temp = current_room_temp
            self.rooms.append(temp_room)
            if self.SQ.serving_num < 3:  # 服务队列未满
                self.SQ.insert(temp_room)
            else:  # 服务队列已满
                self.WQ.insert(temp_room)

            return_room = temp_room
            #  写入数据库
            temp_room.request_time = timezone.now()
            self.request_id += 1
            temp_room.operation = 3
            temp_room.save(force_insert=True)

        return return_room  # 返回房间的状态，目标温度，风速，费率以及费用

    def set_service_num(self, service_num):
        """
        :param service_num:
        :return:
        """
        self.service_num = service_num

    def change_target_temp(self, room_id, target_temp):
        """
        修改目标温度
        :param room_id:
        :param target_temp:
        :return:
        """
        if target_temp < 18:
            target_temp = 18
        if target_temp > 28:
            target_temp = 28
        for room in self.rooms:
            if room.room_id == room_id:
                if room.state == 1:  # 在调度队列中
                    self.SQ.set_target_temp(room_id, target_temp)
                elif room.state == 2:  # 在等待队列中
                    self.WQ.set_target_temp(room_id, target_temp)
                else: room.target_temp = target_temp

                # 写入数据库
                room.request_id = self.request_id
                self.request_id += 1
                room.operation = 1
                room.request_time = timezone.now()
                room.save(force_insert=True)

                return room

    def change_fan_speed(self, room_id, fan_speed):
        """
        处理调风请求
        :param room_id:
        :param fan_speed:
        :return:
        """
        if fan_speed == 1:
            fee_rate = self.fee_rate_h  # 高风速时的费率
        elif fan_speed == 2:
            fee_rate = self.fee_rate_m  # 中风速时的费率
        elif fan_speed < 1:
            fee_rate = self.fee_rate_h
        else:
            fee_rate = self.fee_rate_l  # 低风速时的费率
        for room in self.rooms:
            if room.room_id == room_id:
                if room.state == 1:  # 在调度队列中
                    self.SQ.set_fan_speed(room_id, fan_speed, fee_rate)
                elif room.state == 2:  # 在等待队列中
                    self.WQ.set_fan_speed(room_id, fan_speed, fee_rate)
                else:
                    room.fan_speed = fan_speed
                    room.fee_rate = fee_rate
                # 写入数据库
                room.request_id = self.request_id
                self.request_id += 1
                room.operation = 2
                room.request_time = timezone.now()
                room.save(force_insert=True)

                return room

    def check_room_state(self):
        """
        每分钟查看一次房间状态
        :return:
        """
        timer = threading.Timer(5/6, self.check_room_state)  # 每五秒执行一次check函数,list_room为参数
        timer.start()
        return self.rooms

    def update_room_state(self, room_id):
        """
        每分钟查看一次房间状态
        :param room_id:
        :return:
        """
        for room in self.rooms:
            # print(room.room_id)
            if room.room_id == room_id:
                return room

    def set_para(self, temp_high_limit, temp_low_limit, default_target_temp, fee_rate_h, fee_rate_l, fee_rate_m):
        """
        设置中控机参数
        :param temp_high_limit:
        :param temp_low_limit:
        :param default_target_temp:
        :param fee_rate_h:
        :param fee_rate_l:
        :param fee_rate_m:
        :return:
        """
        self.temp_high_limit = temp_high_limit
        self.temp_low_limit = temp_low_limit
        self.default_target_temp = default_target_temp
        self.fee_rate_h = fee_rate_h
        self.fee_rate_l = fee_rate_l
        self.fee_rate_m = fee_rate_m
        return True

    def start_up(self):
        """
        参数设置完毕，进入READY状态
        :return:
        """
        self.state = 4
        return self.state

    def request_off(self, room_id):
        """
         # 处理房间的关机请求(未开机时，不能发出关机请求)
        :param room_id:
        :return:
        """
        for room in self.rooms:
            if room.room_id == room_id:
                room.current_temp = room.init_temp
                #  关机回到初始温度
                if room.state == 1:  # 在调度队列中
                    room.state = 3
                    self.SQ.delete_room(room)
                elif room.state == 2:  # 在等待队列中
                    room.state = 3
                    self.WQ.delete_room(room)
                else:
                    room.state = 3
                # 写入数据库
                room.request_id = self.request_id
                self.request_id += 1
                room.operation = 4
                room.request_time = timezone.now()
                room.save(force_insert=True)

                # 开启调度函数

                if self.WQ.waiting_num != 0 and self.SQ.serving_num == 2:
                    temp = self.WQ.room_list[0]
                    self.WQ.delete_room(temp)
                    self.SQ.insert(temp)

                elif self.WQ.waiting_num != 0 and self.SQ.serving_num <= 1:
                    i = 1
                    for temp in self.WQ.room_list:
                        if i <= 2:
                            self.WQ.delete_room(temp)
                            self.SQ.insert(temp)
                        i += 1

                elif self.WQ.waiting_num != 0 and self.SQ.serving_num <= 0:
                    i = 1
                    for temp in self.WQ.room_list:
                        if i <= 3:
                            self.WQ.delete_room(temp)
                            self.SQ.insert(temp)
                        i += 1

                return room

    # 达到目标温度后待机的房间启动回温算法
    def back_temp(self, room, mode):  # mode=1制热 mode=2制冷,回温算法0.5℃/min，即0.008℃/s
        if room.state == 4:
            if mode == 1:
                room.current_temp -= 0.008
                if abs(room.target_temp - room.current_temp) > 1:
                    if self.SQ.serving_num < 3:  # 服务队列没满
                        self.SQ.insert(room)
                    else:
                        self.WQ.insert(room)
                timer = threading.Timer(1/6, self.back_temp, [room, 1])  # 每1秒执行一次函数
                timer.start()
            else:
                room.current_temp += 0.008
                if abs(room.target_temp - room.current_temp) > 1 and room.current_temp > room.target_temp:
                    if self.SQ.serving_num < 3:  # 服务队列没满
                        self.SQ.insert(room)
                    else:
                        self.WQ.insert(room)
                timer = threading.Timer(1/6, self.back_temp, [room, 2])  # 每1秒执行一次函数
                timer.start()

    def check_target_arrive(self):
        """
        每分钟，遍历服务队列中的房间，将达到目标温度的房间移出服务队列，状态设为休眠
        :return:
        """
        if self.SQ.serving_num != 0:
            for room in self.SQ.room_list:
                if abs(room.current_temp - room.target_temp) < 0.1 or room.current_temp < room.target_temp:
                    room.state = 4
                    self.SQ.delete_room(room)
                    if self.default_target_temp == 22:
                        self.back_temp(room, 1)
                    else:
                        self.back_temp(room, 2)
        if self.WQ.waiting_num != 0:
            for room in self.WQ.room_list:
                if abs(room.current_temp - room.target_temp) < 0.1 or room.current_temp < room.target_temp:
                    room.state = 4
                    self.WQ.delete_room(room)
                    if self.default_target_temp == 22:
                        self.back_temp(room, 1)
                    else:
                        self.back_temp(room, 2)

        timer = threading.Timer(1/6, self.check_target_arrive)  # 每5秒执行一次check函数
        timer.start()

    def scheduling(self):
        """
        调度算法
        服务队列：先按风速排序，风速相同的情况先入先出
        等待队列：先入先出的时间片调度
        把SQ的第一个加入WQ，WQ的第一个放入SQ末尾
        :return:
        """
        if self.WQ.waiting_num != 0 and self.SQ.serving_num == 3:
            temp = self.SQ.room_list[0]
            self.SQ.delete_room(temp)
            self.WQ.insert(temp)
            temp = self.WQ.room_list[0]
            self.WQ.delete_room(temp)
            self.SQ.insert(temp)

        elif self.WQ.waiting_num != 0 and self.SQ.serving_num == 2:
            temp = self.WQ.room_list[0]
            self.WQ.delete_room(temp)
            self.SQ.insert(temp)

        elif self.WQ.waiting_num != 0 and self.SQ.serving_num <= 1:
            i = 1
            for temp in self.WQ.room_list:
                if i <= 2:
                    self.WQ.delete_room(temp)
                    self.SQ.insert(temp)
                i += 1

        elif self.WQ.waiting_num != 0 and self.SQ.serving_num <= 0:
            i = 1
            for temp in self.WQ.room_list:
                if i <= 3:
                    self.WQ.delete_room(temp)
                    self.SQ.insert(temp)
                i += 1
        timer = threading.Timer(120/6, self.scheduling)  # 每2min执行一次调度函数
        timer.start()


class Server(models.Model):
    """
    名称：服务对象
    作用：服务对象最多仅存在3个，每个服务对象对应一个房间，供调度算法以及温控使用。
    """
    STATE_CHOICE = [
        (1, 'WORKING'),
        (2, 'FREE'),
    ]

    # 服务对象的服务状态
    state = models.IntegerField(verbose_name='服务状态', choices=STATE_CHOICE, default=2)

    # 服务开始时间
    start_time = models.DateField(verbose_name="创建时间", default=timezone.now)

    # 服务对象的服务时长
    serve_time = models.FloatField(verbose_name='服务时长')

    # 服务对象所服务的房间号
    room_id = models.IntegerField(verbose_name='服务房间号')

    # 服务对象所服务房间的目标温度
    target_temp = models.IntegerField(verbose_name='目标温度')

    # 服务对象所服务房间的费用
    fee = models.FloatField(verbose_name='费用')

    # 服务对象所服务房间的费率
    fee_rate = models.FloatField(verbose_name='费率')

    # 服务对象所服务的房间的风速,默认值为2--middle
    fan_speed = models.IntegerField(verbose_name='风速', default=2)

    def set_attribute(self, room_id, start_time, current_room_temp):
        """
        服务对象的初始化，与某一个房间关联起来；
        :param room_id:
        :param start_time:
        :param current_room_temp:
        :return:
        """
        self.room_id = room_id
        self.start_time = start_time
        self.serve_time = 0.0
        self.state = 1  # 状态为working
        self.target_temp = 26
        self.fan_speed = 2  # 默认为中速风2--middle
        self.fee = 0.0
        self.fee_rate = 0.8
        return_list = [self.state, self.target_temp, self.fee_rate, self.fee]
        return return_list

    def change_target_temp(self, target_temp):
        """
        修改正在服务房间的目标温度
        :param target_temp:
        :return:
        """
        self.target_temp = target_temp
        return True

    def change_fan_speed(self, fan_speed):
        """
        修改正在服务房间的风速
        :param fan_speed:
        :return:
        """
        self.fan_speed = fan_speed
        return True

    def delete_server(self):
        """
        删除服务对象与被服务房间的关联
        :return:
        """
        #  将信息写入数据库
        # 。。。
        self.room_id = 0  # 将服务对象设置为空闲
        self.state = 2  # 状态为FREE
        return self.fee

    def set_erve_time(self):
        """
        修改服务时长
        :return:
        """
        self.serve_time = timezone.now() - self.start_time

    def set_fee(self, fee):
        """
        修改被服务房间的费用
        :return:
        """
        self.fee = fee


class Room(models.Model):
    FAN_SPEED = [
        (3, "HIGH"),
        (2, "MIDDLE"),
        (1, "LOW"),
    ]

    ROOM_STATE = [
        (1, "SERVING"),
        (2, "WAITING"),
        (3, "SHUTDOWN"),
        (4, "BACKING")  # 休眠
    ]

    OPERATION_CHOICE = [
        (1, '调温'),
        (2, '调风'),
        (3, '开机'),
        (4, '关机')
    ]

    # 请求号
    request_id = models.IntegerField(verbose_name="请求号", primary_key=True, default=0)

    # 请求发出时间
    request_time = models.DateTimeField(verbose_name="请求发出时间", default=django.utils.timezone.now)

    # 房间号，唯一表示房间
    room_id = models.IntegerField(verbose_name="房间号", default=0)

    # 当前温度
    current_temp = models.FloatField(verbose_name="当前温度", default=0.0)

    # 初始化温度
    init_temp = models.FloatField(verbose_name="初始化温度", default=0.0)

    # 目标温度
    target_temp = models.FloatField(verbose_name="目标温度", default=25.0)

    # 风速
    fan_speed = models.IntegerField(verbose_name='风速', choices=FAN_SPEED, default=2)

    # 房间状态
    state = models.IntegerField(verbose_name='服务状态', choices=ROOM_STATE, default=3)

    # 费率
    fee_rate = models.FloatField(verbose_name='费率', default=0.5)

    # 费用
    fee = models.FloatField(verbose_name='费用', default=0.0)

    # 当前服务时长
    serve_time = models.IntegerField(verbose_name='当前服务时长', default=0)

    # 当前等待时长
    wait_time = models.IntegerField(verbose_name='当前等待时长', default=0)

    # 操作类型
    operation = models.IntegerField(verbose_name='操作类型', choices=OPERATION_CHOICE, default=0)

    # 调度次数
    scheduling_num = models.IntegerField(verbose_name='调度次数', default=0)


class StatisticController(models.Model):
    """
    - 名称：统计控制器
    - 作用：负责读数据库的控制器，为前台生成详单、账单
    """
    sche=[]
    
    def __init__(self):
        self.sche = Scheduler()  # 实例化 ClassB 对象
    @staticmethod
    def reception_login(id, password):
        """
        感觉放在这里不是特别好，应该放在view层
        如何登录请看:https://docs.djangoproject.com/zh-hans/2.2/topics/auth/default/#how-to-log-a-user-in
        :param id:
        :param password:
        :return:
        """

    @staticmethod
    def create_rdr(room_id, begin_date, end_date):
        """
        打印详单
        :param room_id: 房间号
        :param begin_date: 起始日期
        :param end_date: endDay
        :return:    返回详单字典列表
        """
        detail = []
        rdr = Room.objects.filter(room_id=room_id, request_time__range=(begin_date, end_date)).order_by('-request_time')
        last_record = rdr.last()  # 取最早的一条
        first_record = rdr.first()  # 取最新的一条
        for r in rdr:
            dic = {}
            dic.update(request_id=r.request_id,
                       request_time=r.request_time,
                       room_id=r.room_id,
                       operation_type=r.operation,
                       current_temperation=r.current_temp,
                       target_temperation=r.target_temp,
                       fan_speed=r.fan_speed,
                       air_fee=r.fee,
                       fee_rate = "1元/度",
                       total_server_time='')
            detail.append(dic)
        
        # 计算总服务器时间并更新最后一条记录
        if last_record and first_record:  # 确保记录存在
            # 确保总时长不为负，并保留一位小数
            total_server_time1 = abs((last_record.request_time - first_record.request_time).total_seconds())
            total_server_time1 = round(total_server_time1, 1)
            detail[0]['total_server_time'] = str(total_server_time1)  # 用键值对方式更新字典

        # 根据 operation 字段映射操作名称
        operation_mapping = {1: '调温', 2: '调风', 3: '开机', 4: '关机'}
        for item in detail:
            if item['operation_type'] in operation_mapping:
                item['operation_type'] = operation_mapping[item['operation_type']]
        
        # 根据 fan_speed 字段映射操作名称
        fan_mapping = {1: '高速', 2: '中速', 3: '低速'}
        for item in detail:
            if item['fan_speed'] in fan_mapping:
                item['fan_speed'] = fan_mapping[item['fan_speed']]
            #for d in detail:
            #    print(d)
        return detail

    @staticmethod
    def print_rdr(room_id, begin_date, end_date):
        """
        打印详单
        :param room_id: 房间号
        :param begin_date: 起始日期
        :param end_date: endDay
        :return:    返回详单字典列表
        """
        rdr = StatisticController.create_rdr(room_id, begin_date, end_date)
        import csv
        # 文件头，一般就是数据名
        file_header = ["request_id",
                       "request_time",
                       "room_id",
                       "operation_type",
                       "current_temperation",
                       "target_temperation",
                       "fan_speed",
                       "air_fee",
                       "fee_rate",
                       "total_server_time"]

        # 写入数据
        with open("./result/detailed_list.csv", "w")as csvFile:
            writer = csv.DictWriter(csvFile, file_header)
            writer.writeheader()
            # 写入的内容都是以列表的形式传入函数
            for d in rdr:
                writer.writerow(d)

            csvFile.close()
            return True

    from datetime import datetime
    
    def create_bill(self, room_id, begin_date, end_date):
        """
        创建账单
        :param room_id: 房间号
        :param begin_date: 起始日期
        :param end_date: endDay
        :return:
        """
        bill = [room for room in self.sche.rooms if room.room_id == room_id]

        #print("fee=%f" % bill.fee)
        print("room_fee信息：",bill[0].fee)
        room_fee_mapping = {1: 100, 2: 125, 3: 150, 4:200, 5:100}
        
        room_fee = room_fee_mapping.get(room_id, 0)
        # room_fee = room_fee_mapping.get(room_id, 0) + end_date和begin_date转成日期类型，然后
        # 计算时间差（天数）
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        begin_date = datetime.strptime(begin_date, "%Y-%m-%d").date()
        date_diff = abs((end_date - begin_date).days)  # .days 返回天数的整数部分
        room_fee = room_fee * date_diff
        # 计算总费用
        add_fee = room_fee + bill[0].fee
        

        return bill[0].fee, room_fee, add_fee

    
    def print_bill(self,room_id, begin_date, end_date):
        """
        打印账单
        :param room_id: 房间号
        :param begin_date: 起始日期
        :param end_date: endDay
        :return:返回房间的账单费用
        """
        room_id = int(room_id)
        air_fee, room_fee, add_fee = self.create_bill(room_id, begin_date, end_date)

            
        with open('./result/bill.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["room_id", "air_fee","room_fee","add_fee"])
            writer.writerow([room_id, air_fee, room_fee, add_fee])
        return air_fee

    @staticmethod
    def create_report(room_id, type_report, year=-1, month=-1, week=-1):
        """
        创建报告
        :param room_id: 房间号
        :param type_report:报告类型,1为月报表，2为周报表
        :param month: 如果为月报，只需填入对应的月份起始日，例如“2020-5”
        :param week: 终止日期， 如果选择为周报表，则需要填入具体的起始日期“2020-x-x”以及终止日期“2020-x-x”
        :return: 将返回一个pdf报表
        """
        OPERATION_CHOICE = [
            (1, '调温'),
            (2, '调风'),
            (3, '开机'),
            (4, '关机')
        ]
        global operations
        if type_report == 1:
            """经理选择打印月报"""
            try:
                operations = Room.objects.filter(
                    Q(room_id=room_id) & (Q(request_time__year=year) & Q(request_time__month=month))).order_by(
                    '-request_time')
            except ObjectDoesNotExist:
                print("Either the room or time doesn't exist.")
        else:
            """打印周报"""
            try:
                week="  "+str(week)
                operations = Room.objects.filter(
                    Q(room_id=room_id) & (Q(request_time__year=year) & Q(request_time__week=week))).order_by(
                    '-request_time')
            except ObjectDoesNotExist:
                print("Either the room or time doesn't exist.")
        
        # room_weeks = Room.objects.values('request_time__week').distinct() # 打印每个年份值 
        # for week in room_weeks: print("现在的week是："['request_time__week'])
        
        report = {}
        report.update(room_id=room_id)
        # 开关次数
        switch_times = operations.filter(Q(operation=3) | Q(operation=4)).count()
        report.update(switch_times=switch_times)
        # 操作次数
        detailed_num = len(operations)
        report.update(detailed_num=detailed_num)
        # 调温次数
        change_temp_times = operations.filter(operation=1).count()
        report.update(change_temp_times=change_temp_times)
        # 调风次数
        change_fan_times = operations.filter(operation=2).count()
        report.update(change_fan_times=change_fan_times)

        if len(operations) == 0:
            schedule_times = 0
            request_time = 0
            fee = 0
        else:
            # 调度次数
            schedule_times = operations[0].scheduling_num
            # 请求时长
            request_time = operations[0].serve_time
            # 总费用
            fee = operations[0].fee

        report.update(schedule_times=schedule_times)
        report.update(request_time=request_time)
        report.update(fee=fee)

        print(report)
        return report

    @staticmethod
    def print_report(room_id=-1, type_report=1, year=-1, month=-1, week=-1):
        """
        创建报告
        :param room_id: 房间号，如果room_id=-1则输出所有房间的报表
        :param type_report:报告类型,1为月报表，2为周报表
        :param year:年份，不管月报、周报，都应该输入年份
        :param month: 如果为月报，只需填入对应的月份，例如“5”
        :param week: 如果选择为周报表，则需要输出第几周（相对于该年）
        :return: 将返回一个csv报表
        """
        header = [
            'room_id', 'switch_times', 'detailed_num', 'change_temp_times', 'change_fan_times',
            'schedule_times', 'request_time', 'fee'
        ]
        with open('./result/report.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, header)

        writer.writeheader()

        # 如果没有输入房间号，默认输出所有的房间报表
        if room_id == -1:
            for i in range(1, 6):
                report = StatisticController.create_report(room_id, type_report, year, month, week)

                writer.writerow(report)
        else:
            report = StatisticController.create_report(room_id, type_report, year, month, week)

            writer.writerow(report)

        return True

    @staticmethod
    def draw_report(room_id=-1, type_report=1, year=-1, month=-1, week=-1):
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        if room_id == -1:
            global report
            data = []
            rows = []
            
            # 收集报告数据
            for i in range(1, 6):
                report = StatisticController.create_report(i, type_report, year, month, week)
                data.append(list(report.values())[1:-2])
                rows.append('房间' + str(report['room_id']))
            
            columns = list(report.keys())[1:-2]
            rows = tuple(rows)

            # 创建DataFrame
            df = pd.DataFrame(data, columns=columns, index=rows)

            # 创建图形和坐标轴
            fig, ax = plt.subplots(figsize=(15, 6))

            # 绘制每个房间的数据作为折线图
            for i, row in enumerate(rows):
                ax.plot(columns, df.iloc[i], label=row, marker='o', linestyle='-', linewidth=2, markersize=6)

            # 定制网格和坐标轴
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
            ax.set_facecolor('whitesmoke')

            # 设置图表标题
            ax.set_title('各房间报告数据 (折线图)', fontsize=16, fontweight='bold', color='darkblue')

            # 设置x轴和y轴标签
            if(type_report==1):ax.set_xlabel('报告类型: 月报', fontsize=12)
            elif(type_report==2):ax.set_xlabel('报告类型: 周报', fontsize=12)
            ax.set_ylabel('数值', fontsize=12)

            # 设置x轴的中文标签
            x_labels = ['开关次数', '总操作次数', '调温次数', '调风次数','调度次数']  # 根据实际需要修改
            ax.set_xticks(range(len(x_labels)))  # 设置x轴的刻度位置
            ax.set_xticklabels(x_labels, fontsize=10)  # 设置x轴标签为中文

            # 添加图例
            ax.legend(title="房间", title_fontsize=10, fontsize=9, loc='upper left')

            # 调整图表的布局和间距
            plt.subplots_adjust(left=0.1, right=0.9, bottom=0.2, top=0.85)

            # 将图表保存为高分辨率PNG文件
            if(type_report==1):plt.savefig('./result/report_line_plot_month.png', dpi=300)
            elif(type_report==2):plt.savefig('./result/report_line_plot_week.png', dpi=300)
            

            # 显示图表（可选，仅在交互式会话中使用）
            # plt.show()

# def draw_report(room_id=-1, type_report=1, year=-1, month=-1, week=-1):
#     import matplotlib.pyplot as plt
#     import numpy as np
#     import pandas as pd

#     # 如果没有输入房间号，逐个
#     if room_id == -1:
#         global report
#         data = []
#         rows = []
        
#         # 收集报告数据
#         for i in range(1, 6):
#             report = StatisticController.create_report(i, type_report, year, month, week)
#             data.append(list(report.values())[1:-2])
#             rows.append('房间' + str(report['room_id']))
        
#         columns = list(report.keys())[1:-2]
#         rows = tuple(rows)

#         # 创建DataFrame
#         df = pd.DataFrame(data, columns=columns, index=rows)

#         # 创建图形和坐标轴
#         fig, ax = plt.subplots(figsize=(15, 6))

#         # 绘制每个房间的数据作为折线图
#         for i, row in enumerate(rows):
#             ax.plot(columns, df.iloc[i], label=row, marker='o', linestyle='-', linewidth=2, markersize=6)

#         # 定制网格和坐标轴
#         ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
#         ax.set_facecolor('whitesmoke')

#         # 设置图表标题
#         ax.set_title('各房间报告数据 (折线图)', fontsize=16, fontweight='bold', color='darkblue')

#         # 设置x轴和y轴标签
#         ax.set_xlabel('报告类型', fontsize=12)
#         ax.set_ylabel('数值', fontsize=12)

#         # 添加图例
#         ax.legend(title="房间", title_fontsize=10, fontsize=9, loc='upper left')

#         # 调整图表的布局和间距
#         plt.subplots_adjust(left=0.1, right=0.9, bottom=0.2, top=0.85)

#         # 将图表保存为高分辨率PNG文件
#         plt.savefig('./result/report_line_plot.png', dpi=300)

#         # 显示图表（可选，仅在交互式会话中使用）
#         plt.show()