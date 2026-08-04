from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    def get_queryset(self): return Notification.objects.filter(user=self.request.user)

class NotificationReadView(APIView):
    def post(self, request, pk):
        n = Notification.objects.get(pk=pk, user=request.user)
        if not n.read_at:
            n.read_at = timezone.now(); n.save(update_fields=["read_at"])
        return Response(NotificationSerializer(n).data)

class NotificationReadAllView(APIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)
