from django.db import models


class Blacklist(models.Model):
    word = models.CharField(max_length=64)
