# Generated by Django 3.1.2 on 2020-11-01 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20201101_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='gitapp',
            name='port',
            field=models.IntegerField(null=True),
        ),
    ]
