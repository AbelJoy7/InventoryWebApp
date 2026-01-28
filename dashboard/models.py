from django.db import models

# Create your models here.

class Sales(models.Model):
    date = models.DateField()
    product = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product} - {self.date}"


class purchase(models.Model):
    date = models.DateField()
    item = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller_name = models.CharField(max_length=100)
    seller_place = models.CharField(max_length=100)
    seller_phno = models.CharField(max_length=15)
    purchase_total = models.DecimalField(max_digits=10000, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.item} - {self.date}"