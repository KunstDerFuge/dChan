from django.db import models


class JobType(models.TextChoices):
    NEW = 'NEW'
    REVISIT = 'REV'
