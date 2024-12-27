from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class SplitBillGroup(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_groups",  # Avoids conflict with 'auth.User.groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SplitBillGroupMember(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]
    group = models.ForeignKey(
        SplitBillGroup, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="group_memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class Expense(models.Model):
    group = models.ForeignKey(
        SplitBillGroup, on_delete=models.CASCADE, related_name="expenses"
    )
    title = models.CharField(max_length=100)
    total_amount = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
    )
    paid_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="paid_expenses",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Item(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=100)
    price = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name


class ItemShare(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="item_shares")
    share_amount = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=1,
    )

    class Meta:
        unique_together = ("item", "user")

    def __str__(self):
        return f"{self.user.username} - {self.share_amount}"
