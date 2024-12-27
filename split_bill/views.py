from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import Group, User
from django.db.models import Q, Sum
from django.db import transaction

from rest_framework import permissions, viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from split_bill.models import (
    SplitBillGroup,
    SplitBillGroupMember,
    Expense as ExpenseModel,
    Item as ItemModel,
    ItemShare,
)
from split_bill.serializers import (
    GroupSerializer,
    UserSerializer,
    SplitBillGroupSerializer,
    AddGroupMemberSerializer,
    ExpenseSerializer,
    ItemSerializer,
    ItemShareSerializer,
)
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import APIException, PermissionDenied
from django.forms.models import model_to_dict


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class SplitBillGroups(APIView):
    def post(self, request):
        data = request.data.copy()
        data["created_by"] = request.user.id
        serializer = SplitBillGroupSerializer(data=data)

        if serializer.is_valid():
            instance = serializer.save()
            SplitBillGroupMember.objects.create(
                group=instance, user=request.user, role="admin"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, groupId=None):
        try:
            if groupId:
                group = SplitBillGroup.objects.get(id=groupId)

                is_member = SplitBillGroupMember.objects.filter(
                    group=group, user=request.user
                )
                if not (is_member.exists() or request.user.is_superuser):
                    return Response(
                        {"error": "You do not have permission to access this group."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Serialize the group details
                serializer = SplitBillGroupSerializer(
                    group, context={"request": request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                groups = SplitBillGroup.objects.filter(
                    Q(members__user=request.user) | Q(created_by=request.user)
                ).distinct()

                serializer = SplitBillGroupSerializer(
                    groups, many=True, context={"request": request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)

        except APIException as e:
            # Handle other API-related exceptions
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            # Generic fallback for unexpected errors
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    from rest_framework import status


from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django.db.models import Q
from .models import SplitBillGroup, SplitBillGroupMember
from .serializers import SplitBillGroupSerializer


class SplitBillGroups(APIView):
    def post(self, request):
        data = request.data.copy()
        data["created_by"] = request.user.id
        serializer = SplitBillGroupSerializer(data=data, context={"request": request})

        if serializer.is_valid():
            instance = serializer.save()
            SplitBillGroupMember.objects.create(
                group=instance, user=request.user, role="admin"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, groupId=None):
        try:
            if groupId:
                group = SplitBillGroup.objects.get(id=groupId)

                is_member = SplitBillGroupMember.objects.filter(
                    group=group, user=request.user
                )
                if not (is_member.exists() or request.user.is_superuser):
                    return Response(
                        {"error": "You do not have permission to access this group."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Serialize the group details
                serializer = SplitBillGroupSerializer(
                    group, context={"request": request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                groups = SplitBillGroup.objects.filter(
                    Q(members__user=request.user) | Q(created_by=request.user)
                ).distinct()

                serializer = SplitBillGroupSerializer(
                    groups, many=True, context={"request": request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)

        except APIException as e:
            # Handle other API-related exceptions
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            # Generic fallback for unexpected errors
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, groupId):
        try:
            # Fetch the group by ID
            group = SplitBillGroup.objects.get(id=groupId)
            user_member = SplitBillGroupMember.objects.get(
                group=group, user=request.user
            )

            # Ensure the user is the creator of the group or a superuser
            if (
                group.created_by != request.user or user_member.role != "admin"
            ) and not request.user.is_superuser:
                return Response(
                    {"error": "You do not have permission to edit this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            allowed_fields = {
                "name",
            }
            invalid_fields = [
                key for key in request.data.keys() if key not in allowed_fields
            ]

            if invalid_fields:
                return Response(
                    {"error": f"Invalid fields provided: {', '.join(invalid_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SplitBillGroupSerializer(
                group, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except SplitBillGroup.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        except APIException as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, groupId):
        try:
            # Fetch the group by ID
            group = SplitBillGroup.objects.get(id=groupId)

            user_member = SplitBillGroupMember.objects.get(
                group=group, user=request.user
            )

            # Ensure the user is the creator of the group or a superuser
            if (
                group.created_by != request.user or user_member.role != "admin"
            ) and not request.user.is_superuser:
                return Response(
                    {"error": "You do not have permission to delete this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Delete the group
            group.delete()
            return Response(
                {"message": "Group successfully deleted."},
                status=status.HTTP_204_NO_CONTENT,
            )

        except SplitBillGroup.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except APIException as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SplitBillGroupMembers(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Add Group Member
        try:
            serializer = AddGroupMemberSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            group = SplitBillGroup.objects.get(id=data["group_id"])

            # Check if the user is a member of the group
            is_member = SplitBillGroupMember.objects.filter(
                group=group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You are not a member of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if the requesting user is an admin of the group
            requesting_user_member = SplitBillGroupMember.objects.get(
                group=group, user=request.user
            )

            if requesting_user_member.role != "admin" and not request.user.is_superuser:
                return Response(
                    {
                        "error": "You do not have permission to add members to this group."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if the user to be added is already a member of the group
            if SplitBillGroupMember.objects.filter(
                group=group, user_id=data["member_user_id"]
            ).exists():
                return Response(
                    {"error": "User is already a member of this group."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Add the user to the group
            SplitBillGroupMember.objects.create(
                group=group, user_id=data["member_user_id"], role="member"
            )
            return Response(
                {"message": "Member added successfully."},
                status=status.HTTP_201_CREATED,
            )

        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred: " + str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request):
        try:
            # Fetch groups created by the authenticated user
            groups = SplitBillGroup.objects.filter(created_by=request.user)

            # Serialize the QuerySet
            serializer = SplitBillGroupSerializer(groups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except APIException as e:
            # Handle other API-related exceptions
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            # Generic fallback for unexpected errors
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, groupId, memberId):
        # remove member from group
        try:
            # Fetch the group by ID
            group = SplitBillGroup.objects.get(id=groupId)
        except SplitBillGroup.DoesNotExist:
            return Response(
                {"error": "Group not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Check if the user to be removed exists in the group
            user_member = SplitBillGroupMember.objects.get(
                group=group, user_id=memberId
            )
        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"error": f"Member with ID {memberId} is not part of this group."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Check if the requesting user is a member of the group
            requesting_user_member = SplitBillGroupMember.objects.get(
                group=group, user=request.user
            )
        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check permissions
        if (
            group.created_by != request.user or requesting_user_member.role != "admin"
        ) and not request.user.is_superuser:
            return Response(
                {
                    "error": "You do not have permission to remove members from this group."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Proceed to remove the member
        user_member.delete()
        return Response(
            {"message": "Member removed successfully."},
            status=status.HTTP_200_OK,
        )


class Expense(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data["total_amount"] = 0
        serializer = ExpenseSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        isUserMember = SplitBillGroupMember.objects.filter(
            user=request.user, group_id=data["group"]
        ).exists()

        if not isUserMember and not request.user.is_superuser:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, groupId):
        try:
            # Fetch group by ID
            group = SplitBillGroup.objects.get(id=groupId)

            # Check if the user is a member of the group
            is_member = SplitBillGroupMember.objects.filter(
                group=group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {
                        "error": "You do not have permission to view expenses in this group."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Fetch expenses for the group
            expenses = Expense.objects.filter(group=group)
            serializer = ExpenseSerializer(
                expenses, many=True, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except SplitBillGroup.DoesNotExist:
            return Response(
                {"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpenseDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, expenseId):
        try:

            expense = ExpenseModel.objects.get(id=expenseId)

            # Check if the user is a member of the group associated with the expense
            is_member = SplitBillGroupMember.objects.filter(
                group=expense.group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You do not have permission to view this expense."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Serialize the expense details
            serializer = ExpenseSerializer(expense, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ExpenseModel.DoesNotExist:
            return Response(
                {"error": "Expense not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, expenseId):
        expense = ExpenseModel.objects.get(id=expenseId)
        is_member = SplitBillGroupMember.objects.filter(
            group=expense.group, user=request.user
        ).exists()

        if not is_member and not request.user.is_superuser:
            return Response(
                {"error": "You do not have permission to delete this expense."},
                status=status.HTTP_403_FORBIDDEN,
            )

        expense.delete()
        return Response(
            {"message": "Expense deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class Item(APIView):
    def post(self, request, expenseId):
        try:
            is_member = SplitBillGroupMember.objects.filter(
                group__expenses__id=expenseId, user=request.user
            ).exists()
            data = request.data.copy()
            data["expense"] = expenseId
            serializer = ItemSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You are not a member of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            with transaction.atomic():

                serializer.save()

                expense = ExpenseModel.objects.get(id=expenseId)

                total_amount = expense.items.aggregate(Sum("price"))["price__sum"]
                expense.total_amount = total_amount
                expense.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except SplitBillGroupMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, expenseId):
        try:
            # Fetch expense by ID
            expense = ExpenseModel.objects.get(id=expenseId)

            # Check if the user is a member of the group associated with the expense
            is_member = SplitBillGroupMember.objects.filter(
                group=expense.group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You do not have permission to view this expense."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Fetch items for the expense
            items = ItemModel.objects.filter(expense=expense)
            serializer = ItemSerializer(items, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ExpenseModel.DoesNotExist:
            return Response(
                {"error": "Expense not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItemDetail(APIView):
    def put(self, request, itemId):
        try:
            item = ItemModel.objects.get(id=itemId)
            is_member = SplitBillGroupMember.objects.filter(
                group=item.expense.group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You are not a member of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    # Check if price is changed
                    if "price" in request.data:
                        expense = item.expense
                        total_amount = expense.items.aggregate(Sum("price"))[
                            "price__sum"
                        ]
                        expense.total_amount = total_amount
                        expense.save()

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ItemModel.DoesNotExist:
            return Response(
                {"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, itemId):
        try:
            item = ItemModel.objects.get(id=itemId)
            is_member = SplitBillGroupMember.objects.filter(
                group=item.expense.group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You are not a member of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            with transaction.atomic():
                item.delete()
                expense = item.expense
                total_amount = expense.items.aggregate(Sum("price"))["price__sum"]
                expense.total_amount = total_amount
                expense.save()

            return Response(
                {"message": "Item deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )

        except ItemModel.DoesNotExist:
            return Response(
                {"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItemShareView(APIView):
    def post(self, request, itemId):
        try:
            # Step 1: Retrieve the item based on itemId
            item = ItemModel.objects.get(id=itemId)

            # Step 2: Get the list of user_ids to check and add shares
            user_ids = request.data.get("user_ids", [])
            if not user_ids:
                return Response(
                    {"error": "No user IDs provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Step 3: Check if the user_ids are valid members of the group
            group = item.expense.group
            valid_members = SplitBillGroupMember.objects.filter(
                group=group, user__id__in=user_ids
            )

            if valid_members.count() != len(user_ids):
                return Response(
                    {"error": "One or more users are not members of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Step 4: Remove all existing shares for this item
            ItemShare.objects.filter(item=item).delete()

            # Step 5: Calculate the new share_amount based on the number of users
            valid_user_count = valid_members.count()

            # Step 6: Start a transaction to ensure all operations are atomic
            with transaction.atomic():
                # Step 7: Add new share amounts for each valid user
                for user_id in user_ids:
                    # Create new share records for each user
                    item_share = ItemShare(item=item, user_id=user_id)
                    item_share.share_amount = round(
                        1 / valid_user_count, 2
                    )  # Divide equally among all users
                    item_share.save()

            # Step 8: Return success response
            return Response(
                {"message": "Item shares updated successfully."},
                status=status.HTTP_200_OK,
            )

        except ItemModel.DoesNotExist:
            return Response(
                {"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, itemId):
        try:
            # Fetch item by ID
            item = ItemModel.objects.get(id=itemId)

            # Check if the user is a member of the group associated with the item
            is_member = SplitBillGroupMember.objects.filter(
                group=item.expense.group, user=request.user
            ).exists()

            if not is_member and not request.user.is_superuser:
                return Response(
                    {"error": "You do not have permission to view this item."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Fetch shares for the item
            shares = ItemShare.objects.filter(item=item)
            serializer = ItemShareSerializer(shares, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ItemModel.DoesNotExist:
            return Response(
                {"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
