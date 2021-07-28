# Generated by Django 3.2.3 on 2021-07-27 23:28

import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_alter_post_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(editable=False, null=True),
        ),
    ]