
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('request_id', models.IntegerField(default=0, primary_key=True, serialize=False, verbose_name='请求号')),
                ('request_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='请求发出时间')),
                ('room_id', models.IntegerField(default=0, verbose_name='房间号')),
                ('current_temp', models.FloatField(default=0.0, verbose_name='当前温度')),
                ('init_temp', models.FloatField(default=0.0, verbose_name='初始化温度')),
                ('target_temp', models.FloatField(default=25.0, verbose_name='目标温度')),
                ('fan_speed', models.IntegerField(choices=[(3, 'HIGH'), (2, 'MIDDLE'), (1, 'LOW')], default=2, verbose_name='风速')),
                ('state', models.IntegerField(choices=[(1, 'SERVING'), (2, 'WAITING'), (3, 'SHUTDOWN'), (4, 'BACKING')], default=3, verbose_name='服务状态')),
                ('fee_rate', models.FloatField(default=0.8, verbose_name='费率')),
                ('fee', models.FloatField(default=0.0, verbose_name='费用')),
                ('serve_time', models.IntegerField(default=0, verbose_name='当前服务时长')),
                ('wait_time', models.IntegerField(default=0, verbose_name='当前等待时长')),
                ('operation', models.IntegerField(choices=[(1, '调温'), (2, '调风'), (3, '开机'), (4, '关机')], default=0, verbose_name='操作类型')),
                ('scheduling_num', models.IntegerField(default=0, verbose_name='调度次数')),
            ],
        ),
        migrations.CreateModel(
            name='Scheduler',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.IntegerField(choices=[(1, 'WORKING'), (2, 'SHUTDOWN'), (3, 'SETMODE'), (4, 'READY')], default=2, verbose_name='中控机状态')),
                ('temp_high_limit', models.IntegerField(default=0, verbose_name='最高温度限制')),
                ('temp_low_limit', models.IntegerField(default=0, verbose_name='最低温度限制')),
                ('default_target_temp', models.IntegerField(choices=[(22, '制热'), (25, '制冷')], default=25, verbose_name='默认目标温度')),
                ('fee_rate_h', models.FloatField(default=1.0, verbose_name='高风速费率')),
                ('fee_rate_l', models.FloatField(default=0.5, verbose_name='低风速费率')),
                ('fee_rate_m', models.FloatField(default=0.8, verbose_name='中风速费率')),
            ],
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.IntegerField(choices=[(1, 'WORKING'), (2, 'FREE')], default=2, verbose_name='服务状态')),
                ('start_time', models.DateField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('serve_time', models.FloatField(verbose_name='服务时长')),
                ('room_id', models.IntegerField(verbose_name='服务房间号')),
                ('target_temp', models.IntegerField(verbose_name='目标温度')),
                ('fee', models.FloatField(verbose_name='费用')),
                ('fee_rate', models.FloatField(verbose_name='费率')),
                ('fan_speed', models.IntegerField(default=2, verbose_name='风速')),
            ],
        ),
        migrations.CreateModel(
            name='ServingQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serving_num', models.IntegerField(default=0, verbose_name='服务对象数')),
            ],
        ),
        migrations.CreateModel(
            name='StatisticController',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='WaitingQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('waiting_num', models.IntegerField(default=0, verbose_name='等待对象数')),
            ],
        ),
    ]
