from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import json

from django.shortcuts import get_object_or_404 
from ..Models.chat import AIConsultation, Conversation, PatientQuery
from ..Serializers.chat import ChatSerializer, AllConversationSerializer, ConversationSerializer
# from ..AI.aiReply import get_AI_reply
from ..AI.aiReply import HealthCareAsistant

class AllConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Conversation.objects.filter(user=request.user).order_by('-created_at')
        serializer = AllConversationSerializer(data, many=True)
        return Response(serializer.data)
    
class CreateConversationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        obj = Conversation.objects.create(user=request.user)
        return Response({'id': obj.id}, status=status.HTTP_200_OK)
    
class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        data = get_object_or_404(Conversation, id=id, user=request.user)


        serializer = ConversationSerializer(data)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request, id):
        serializer = ChatSerializer(data=request.data, context={'conv_id': id})
        
        if serializer.is_valid():
            query = serializer.save()

        reply_txt = HealthCareAsistant.get_reply(request.data.get('content'), id)

        # reply_txt = f"you said reply {request.data.get('content')}"

        AIConsultation.objects.create(query=query, response=json.dumps(reply_txt))

        return Response({
            "ai_reply": reply_txt
        }, status=status.HTTP_200_OK) 


