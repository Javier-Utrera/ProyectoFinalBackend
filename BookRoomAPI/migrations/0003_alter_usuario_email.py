# Generated by Django 5.2 on 2025-04-14 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BookRoomAPI', '0002_alter_usuario_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email address'),
        ),
    ]
