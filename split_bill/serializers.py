from django.contrib.auth.models import Group, User
from split_bill.models import (
    SplitBillGroup,
    SplitBillGroupMember,
    Expense,
    Item,
    ItemShare,
)
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["id", "url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class SplitBillGroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Use the UserSerializer to include user details

    class Meta:
        model = SplitBillGroupMember
        fields = ["user", "role", "joined_at"]


class SplitBillGroupSerializer(serializers.ModelSerializer):
    members = SplitBillGroupMemberSerializer(many=True, read_only=True)

    class Meta:
        model = SplitBillGroup
        fields = ["id", "name", "created_by", "created_at", "members"]


class AddGroupMemberSerializer(serializers.Serializer):
    member_user_id = serializers.IntegerField(required=True)
    group_id = serializers.IntegerField(required=True)


class ItemShareSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Use the UserSerializer to include user details

    class Meta:
        model = ItemShare
        fields = ["user", "share_amount"]


class ItemSerializer(serializers.ModelSerializer):
    shares = ItemShareSerializer(many=True, read_only=True)  # Include item shares

    class Meta:
        model = Item
        fields = ["id", "name", "price", "shares"]


class ExpenseSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "group",
            "title",
            "total_amount",
            "paid_by",
            "created_at",
            "items",
        ]
        read_only_fields = ["created_at"]

    def validate_group(self, group):
        request = self.context.get("request")
        if (
            not SplitBillGroupMember.objects.filter(
                group=group, user=request.user
            ).exists()
            and not request.user.is_superuser
        ):
            raise serializers.ValidationError("You are not a member of this group.")
        return group
