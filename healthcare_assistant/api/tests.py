from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .Models.chat import Conversation


class ChatApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_conversation_returns_id(self):
        response = self.client.post("/api/chat/create/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertTrue(
            Conversation.objects.filter(id=response.data["id"], user=self.user).exists()
        )

    @patch("api.Views.chat.get_AI_reply", return_value="Mock AI reply")
    def test_post_message_saves_query_and_reply(self, mocked_reply):
        conversation = Conversation.objects.create(user=self.user)

        response = self.client.post(
            f"/api/chat/{conversation.id}/",
            {"content": "I have a fever"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ai_reply"], "Mock AI reply")

        conversation.refresh_from_db()
        query = conversation.queries.get()
        self.assertEqual(query.content, "I have a fever")
        self.assertEqual(query.aiconsultation.response, "Mock AI reply")
        self.assertEqual(conversation.title, "I have a fever")
        mocked_reply.assert_called_once_with("I have a fever")

    def test_conversation_detail_is_scoped_to_owner(self):
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="secret123",
        )
        foreign_conversation = Conversation.objects.create(user=other_user)

        response = self.client.get(f"/api/chat/{foreign_conversation.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
