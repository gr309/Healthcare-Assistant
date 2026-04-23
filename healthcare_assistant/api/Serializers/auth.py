from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from ..utils import generate_username

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}} 

    def validate_email(self, value):
        if User.objects.filter(email=value).exists() :
            raise serializers.ValidationError("Email already registed. Please Login.")
        return value    
    
    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        username = generate_username(email)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        Token.objects.create(user=user)

        return user
    
class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
