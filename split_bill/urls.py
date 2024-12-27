from django.urls import path
from . import views

urlpatterns = [
    path("groups/", views.SplitBillGroups.as_view(), name="split-bill-group"),
    path(
        "groups/<int:groupId>",
        views.SplitBillGroups.as_view(),
        name="split_bill_group_detail",
    ),
    path(
        "groups/<int:groupId>/expenses", views.Expense.as_view(), name="group-expenses"
    ),
    path(
        "group-member",
        views.SplitBillGroupMembers.as_view(),
        name="split_bill_group_member",
    ),
    path("expenses/", views.Expense.as_view(), name="expenses"),
    path("expenses/<int:expenseId>", views.ExpenseDetail.as_view(), name="expenses"),
    path("expenses/<int:expenseId>/items", views.Item.as_view(), name="items"),
    path("items/<int:itemId>", views.ItemDetail.as_view(), name="items"),
    path(
        "items/<int:itemId>/shares", views.ItemShareView.as_view(), name="item shares"
    ),
]
