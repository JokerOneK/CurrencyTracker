# from django.contrib.auth.models import User
from users.models import User
from django.db import models

class Assignment(models.Model):

    first_term = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, blank=False
    )

    second_term = models.DecimalField(
        max_digits=5, decimal_places=2, null=False, blank=False
    )

    # sum should be equal to first_term + second_term
    # its value will be computed in Celery
    sum = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


class Currency(models.Model):
    char_code = models.CharField(max_length=5)


class CurrencyData(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class UserCurrency(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    threshold = models.DecimalField(max_digits=8, decimal_places=4)

