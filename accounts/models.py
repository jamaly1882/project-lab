from django.db import models
from django.contrib.auth.models  import User

from django.db.models.signals import post_save
from django.core.signals import request_finished
from django.dispatch import receiver

class Profile(models.Model):
     ROLE_CHOICES = (
          ("رئيس قسم مساحة", "رئيس قسم مساحة"),
          ("مهندس مساحة", "مهندس مساحة"),
          ("منسق قسم مساحة", "منسق قسم مساحة"),
          ("مدير إدارة المساحة", "مدير إدارة المساحة"),
     )

     user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
     city=models.ForeignKey('City',related_name='user_city',on_delete=models.CASCADE ,null=True, blank=True)
     role=models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True, default="", verbose_name="الدور")
     phone_number=models.CharField(max_length=100)
     # المديرية (من جدول mahfth) التي يتبع لها المستخدم
     mahfth=models.ForeignKey(
          'masha.Mahfth',
          related_name='user_profile_mahfth',
          on_delete=models.SET_NULL,
          null=True,
          blank=True,
          verbose_name='المديرية',
     )
     
     
     @receiver(post_save,sender=User)
     def create_user_profile(sender,instance,created,**kwargs):
        if created:
            Profile.objects.create(user=instance)
            
     def __str__(self):
           return str(self.user)

class City(models.Model):
     
     city=models.CharField(max_length=200)
     phone_number=models.CharField(max_length=200)

     # المديرية المرتبطة بالمدينة (إن وجدت)
     mahfth=models.ForeignKey(
          'masha.Mahfth',
          related_name='city_mahfth',
          on_delete=models.SET_NULL,
          null=True,
          blank=True,
          verbose_name='المديرية',
     )
    
     def __str__(self):
           return   self.city
