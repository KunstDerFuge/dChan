# Generated by Django 3.2.3 on 2022-03-25 09:57

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0022_auto_20220320_2348'),
    ]

    operations = [
        migrations.AddField(
            model_name='textboardpost',
            name='sock_of',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), null=True, size=None),
        ),
    ]
