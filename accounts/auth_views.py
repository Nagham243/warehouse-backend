from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser,FormParser

from .serializers import (
    PasswordChangeSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    VendorRegistrationSerializer,
)
from activity_logs.utils import log_activity


@method_decorator(ensure_csrf_cookie, name='get')
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            token = get_token(request)
            return Response({'csrfToken': token})
        except Exception as e:
            import traceback
            print(f"Error in CSRFTokenView: {e}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=500)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle login authentication"""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                return Response(
                    {'error': 'Your account has been suspended. Please contact the administrator.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            login(request, user)

            log_activity(
                user=user,
                activity_type='login',
                object_type='Session',
            )

            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        log_activity(
            user=request.user,
            activity_type='logout',
            object_type='Session',
        )

        logout(request)

        return Response({'success': True})


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            log_activity(
                user=user,
                activity_type='update',
                object_type='Password',
            )

            return Response({'success': 'Password changed successfully'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


class RegistrationView(APIView):
    """
    View for user and vendor registration
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]  # Add this to handle file uploads

    def post(self, request, *args, **kwargs):
        """
        Handle user and vendor registration
        """
        user_type = request.data.get('user_type', 'regular')

        if user_type == 'vendor':
            serializer = VendorRegistrationSerializer(data=request.data)
        else:
            serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = serializer.save()

                log_activity(
                    user=user,
                    activity_type='create',
                    object_type='User',
                    details={
                        'username': user.username,
                        'email': user.email,
                        'user_type': user.user_type
                    }
                )

                user_details = UserDetailSerializer(user).data
                return Response(user_details, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Handle user login"""
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': getattr(user, 'user_type', None),
            },
            'csrfToken': get_token(request)
        })
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
def logout_view(request):
    """Handle user logout"""
    logout(request)
    return Response({'success': True})