from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant
from .serializers import RestaurantSerializer

class RestaurantStatusView(APIView):
    # permission_classes = [IsAdminUser]  # only admin/staff can access

    def get(self, request):
        restaurant = Restaurant.objects.first()
        if not restaurant:
            return Response({"error": "No restaurant found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RestaurantSerializer(restaurant)
        return Response(serializer.data)

    def patch(self, request):
        restaurant = Restaurant.objects.first()
        if not restaurant:
            return Response({"error": "No restaurant found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RestaurantSerializer(
            restaurant,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

