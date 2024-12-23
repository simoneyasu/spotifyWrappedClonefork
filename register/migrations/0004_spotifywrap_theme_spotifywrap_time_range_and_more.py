# Generated by Django 5.1.2 on 2024-11-13 21:29

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0003_spotifywrap'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifywrap',
            name='theme',
            field=models.CharField(choices=[('halloween', 'Halloween'), ('christmas', 'Christmas'), ('None', 'None')], default='None', max_length=20),
        ),
        migrations.AddField(
            model_name='spotifywrap',
            name='time_range',
            field=models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('long', 'Long')], default='long', max_length=10),
        ),
        migrations.AddField(
            model_name='spotifywrap',
            name='wrap_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
