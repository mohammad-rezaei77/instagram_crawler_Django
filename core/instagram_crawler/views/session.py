from instagrapi import Client
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram_crawler.models import Session
from instagram_crawler.serializers import SessionSerializer

PROXY = f"{"http://89.238.132.188"}:{"3128"}"


class CreateSessionAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")

        if not username:
            return Response(
                {"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cl = Client()
            cl.set_proxy(PROXY)

            session = Session.objects.get(username=username)
            cl.login(session.username, session.password)

            session_data = cl.get_settings()
            session.session_data = session_data
            session.is_block = False
            session.is_temp_block = False
            session.is_challenge = False
            session.number_of_use = 0
            session.save()

            return Response(
                {"message": f"Session created and stored for user: {username}"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            if "challenge" in str(e):
                challenge_data = cl.last_json
                session = Session.objects.get(username=username)
                session.challenge_data = challenge_data
                session.save()

                return Response(
                    {
                        "error": "Verification required. Send the verification code using the provided endpoint."
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class ResolveChallengeAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        code = request.data.get("code")

        if not username or not code:
            return Response(
                {"error": "Username and code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = Session.objects.get(username=username)
            if not session.challenge_data:
                return Response(
                    {"error": "No challenge data found for this user."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            cl = Client()
            cl.set_settings(session.session_data)
            cl.challenge_code_send(session.challenge_data["step_data"]["contact_point"])
            cl.challenge_code_verify(code)

            # ذخیره جلسه پس از تأیید
            session_data = cl.get_settings()
            session.session_data = session_data
            session.challenge_data = None  # پاک کردن اطلاعات چالش
            session.save()

            return Response(
                {"message": "Challenge resolved and session updated."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionListCreateView(generics.ListCreateAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
