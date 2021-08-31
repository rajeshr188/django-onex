from django.db import models
from users.models import CustomUser
# Create your models here.
class Company(models.Model):
    created = models.DateField()
    name = models.CharField(max_length=100)
    address = models.TextField(max_length=500)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    mobileno = models.CharField(max_length=11)
    is_active = models.BooleanField(default=False)
    members = models.ManyToManyField(
        CustomUser,
        through='Membership',
        through_fields=('company', 'user'),
    )
    class Meta:
        ordering = ['name']
    def __str__(self):
        return f"{self.name} {self.address}"

class CompanyOwner(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    
class Membership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default = False)
    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="membership_invites",
    )
    invite_reason = models.CharField(max_length=64)
