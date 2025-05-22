from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsSuperAdmin


from .serializers import (
    UserDetailSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer
)




class SuperAdminProfileView(APIView):
    """
    API view for superadmin to manage their own profile
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        """
        Get the currently logged in superadmin's profile
        """
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """
        Update the currently logged in superadmin's profile
        """
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(UserDetailSerializer(user).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuperAdminPasswordChangeView(APIView):
    """
    API view for superadmin to change their password
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
