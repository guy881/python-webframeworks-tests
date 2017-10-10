from django.db import models

# Create your models here.


class ExampleModel(models.Model):
	foo = models.CharField(max_length=32, blank=True)
	bar = models.CharField(max_length=64, blank=True)
