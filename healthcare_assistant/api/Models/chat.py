from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=300, default="New Conversation")
    analization = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
class PatientQuery(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, 
        related_name='queries',    
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AIConsultation(models.Model):
    query = models.OneToOneField(PatientQuery, on_delete=models.CASCADE, related_name='aiconsultation')
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)