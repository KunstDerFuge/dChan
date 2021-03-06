# Generated by Django 3.2.3 on 2021-08-04 10:44

import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=12, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thread_id', models.IntegerField()),
                ('post_id', models.IntegerField()),
                ('author', models.CharField(max_length=180)),
                ('poster_hash', models.CharField(max_length=12)),
                ('subject', models.CharField(max_length=150)),
                ('body', models.TextField()),
                ('drop_no', models.PositiveSmallIntegerField(default=0)),
                ('timestamp', models.DateTimeField()),
                ('tripcode', models.CharField(default=None, max_length=30)),
                ('is_op', models.BooleanField(default=False)),
                ('links', models.JSONField(default=dict)),
                ('search_vector', django.contrib.postgres.search.SearchVectorField(editable=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='posts.board')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='posts.platform')),
                ('reply_to', models.ManyToManyField(related_name='replies', to='posts.Post')),
            ],
        ),
        migrations.AddField(
            model_name='board',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boards', to='posts.platform'),
        ),
        migrations.AddConstraint(
            model_name='post',
            constraint=models.UniqueConstraint(fields=('platform', 'board', 'post_id'), name='unique_post'),
        ),
        migrations.AddConstraint(
            model_name='board',
            constraint=models.UniqueConstraint(fields=('platform', 'name'), name='unique_board'),
        ),
    ]
