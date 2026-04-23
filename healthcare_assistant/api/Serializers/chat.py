from rest_framework import serializers
from django.shortcuts import get_object_or_404

from ..Models.chat import PatientQuery, AIConsultation, Conversation
import json


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientQuery
        fields = ['content']


    def create(self, validated_data):
        content = validated_data.get('content')
        conv_id = self.context.get('conv_id')
        conversation = get_object_or_404(Conversation, id=conv_id)
        query = PatientQuery.objects.create(conversation=conversation, content=content)
        return query

class AllConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title']

class AIConsultationerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConsultation
        fields = ['response']

class PatientQuerySerializer(serializers.ModelSerializer):
    ai_consultation = AIConsultationerializer(source='aiconsultation', read_only=True)
    class Meta:
        model = PatientQuery
        fields = ['content', 'ai_consultation']
 

class ConversationSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'messages',]

    def get_messages(self, obj):
        messages = []

        for query in obj.queries.all().order_by('created_at'):
            message = {
                'query': query.content,
                'response': None
            }
            if hasattr(query, 'aiconsultation') and query.aiconsultation:
                raw = query.aiconsultation.response

                try:
                    message['response'] = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    message['response'] = None


            # if hasattr(query, 'aiconsultation') and query.aiconsultation:
            #     message['response'] = json.loads(query.aiconsultation.response)

            messages.append(message)

        return messages

    
