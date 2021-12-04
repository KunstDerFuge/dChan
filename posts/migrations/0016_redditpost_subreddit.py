# Generated by Django 3.2.3 on 2021-12-03 22:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0015_post_source'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subreddit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=24)),
            ],
        ),
        migrations.CreateModel(
            name='RedditPost',
            fields=[
                ('timestamp', models.DateTimeField()),
                ('edited', models.DateTimeField(blank=True, default=None, null=True)),
                ('author_flair_text', models.CharField(default=None, max_length=64, null=True)),
                ('stickied', models.BooleanField()),
                ('scraped_on', models.DateTimeField()),
                ('permalink', models.URLField()),
                ('score', models.IntegerField()),
                ('post_hint', models.CharField(max_length=12, null=True)),
                ('subject', models.CharField(max_length=250)),
                ('author', models.CharField(max_length=24)),
                ('author_fullname', models.CharField(max_length=14)),
                ('body', models.TextField()),
                ('url', models.URLField(null=True)),
                ('no_follow', models.BooleanField()),
                ('locked', models.BooleanField()),
                ('is_op', models.BooleanField()),
                ('is_submitter', models.BooleanField()),
                ('is_self', models.BooleanField()),
                ('num_comments', models.PositiveIntegerField()),
                ('link_id', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('parent_id', models.CharField(max_length=10, null=True)),
                ('subreddit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='posts.subreddit')),
            ],
        ),
    ]
