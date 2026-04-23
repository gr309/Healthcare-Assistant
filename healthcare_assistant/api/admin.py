from django.contrib import admin
from .models import *

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title')

admin.site.register( Conversation, ConversationAdmin)


class PatientQueryAdmin(admin.ModelAdmin):
    list_display = ('content', 'created_at', )

admin.site.register(PatientQuery, PatientQueryAdmin)

class AIConsultationAdmin(admin.ModelAdmin):
    list_display = ('query', 'response', 'created_at', )

admin.site.register( AIConsultation, AIConsultationAdmin)

