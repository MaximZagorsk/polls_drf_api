from django.db import models
import os
import binascii

class User(models.Model):
    key = models.CharField('Key',max_length=40,unique=True)
    created = models.DateTimeField('Created',auto_now_add=True)

    def save(self,*args,**kwargs):
        if not self.key:
            key = self.generate_key()
            self.key = key
        return super().save(*args,**kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return f'{self.id,self.key}'