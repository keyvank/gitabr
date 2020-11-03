from django.db import models

class GitApp(models.Model):
    url = models.URLField()
    root = models.FileField()
