from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema
from .models import User
from .serializers import UserSerializer


@extend_schema(tags=["Users"])
class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
