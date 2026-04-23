from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated

from ..Serializers.auth import SigninSerializer, SignupSerializer


class SignupView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save() 
            token, created = Token.objects.get_or_create(user=user)


            return Response({
                "username" : user.username, 
                "email" : user.email,
                "token" : token.key
            }, status=status.HTTP_201_CREATED)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    """
    {
        "email" : "user@gmail.com",
        "password" : "userpass"
    }
    """


class SigninView(APIView):
    def post(self, request):
        serilizer = SigninSerializer(data=request.data)
        serilizer.is_valid(raise_exception=True) 

        email = serilizer.validated_data['email']
        password = serilizer.validated_data['password']
        try : 
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except:
            None

        if not user:
            return Response({"details": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "username" : user.username,
            "token": token.key
        }, status=status.HTTP_200_OK)


class SignoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.user.auth_token.delete()

        return Response({"message" : "Logged out"}, status=status.HTTP_200_OK)