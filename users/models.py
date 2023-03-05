from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    pass
    # workspace = models.ForeignKey('company.Company',on_delete = models.CASCADE,
    #                 null = True,blank = True)

    def __str__(self):
        return self.email
