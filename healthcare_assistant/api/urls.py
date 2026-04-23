from django.urls import path
from .Views.auth import SignupView, SigninView, SignoutView
from .Views.chat import  ConversationView, AllConversationView, CreateConversationView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('signin/', SigninView.as_view()),
    path('signout/', SignoutView.as_view()),

    path('chat-list/', AllConversationView.as_view()),
    path('chat/create/', CreateConversationView.as_view()),
    path('chat/<int:id>/', ConversationView.as_view()),
    # path('chat/', ConversationView.as_view()),
    

]