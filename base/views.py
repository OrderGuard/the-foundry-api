from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
# Response
from utils.response_transform import send_response

@api_view(['GET'])
def getRoutes(request):
    """
    Return a list of available API routes.

    """
    routes = [
        'api/token',
        'api/token/refresh',
        'api/auth/register',
        'api/auth/logout'
    ]

    return Response(routes)

@api_view(['POST'])
def register_view(request):
    """
    Register a new user.

    POST:
        Body (JSON):
            - username (str): Required.
            - email (str): Valid email address, required.
            - password (str): Required, minimum 6 characters.
            - confirm_password (str): Must match `password`.

        Returns:
            - Success message with registered username and email on success.
            - Error message if any validation fails.
    """
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    # Check required fields
    if not username or not email or not password or not confirm_password:
        return send_response({
            'status': 'error',
            'message': 'All fields are required: username, email, password, confirm_password.'
        })

    # Email format validation
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        return send_response({
            'status': 'error',
            'message': 'Invalid email format.'
        })

    # Password confirmation
    if password != confirm_password:
        return send_response({
            'status': 'error',
            'message': 'Passwords do not match.'
        })

    # Password length (optional)
    if len(password) < 6:
        return send_response({
            'status': 'error',
            'message': 'Password must be at least 6 characters long.'
        })

    # Unique username or email check
    if User.objects.filter(username=username).exists():
        return send_response({
            'status': 'error',
            'message': 'Username already exists.'
        })
    if User.objects.filter(email=email).exists():
        return send_response({
            'status': 'error',
            'message': 'Email already registered.'
        })

    # Create new user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    return send_response({
        'status': 'success',
        'message': 'User registered successfully.',
        'user': {
            'username': user.username,
            'email': user.email,
        }
    }, status_code=201)


@api_view(['POST'])
def logout_view(request):
    """
    Logout current user by deleting refresh token cookie.

    """
    response = Response({
        'status': 'success',
        'message': 'Logged out successfully.'
    })

    # Clear refresh token cookie
    response.delete_cookie('refresh_token')

    return response

