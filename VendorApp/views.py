# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from VendorApp.serializers.hp_serializer import HistoricalPerformanceSerializer
from .models import HistoricalPerformance, PurchaseOrder, Vendor
from .serializers.vendor_serializer import VendorSerializer
from .serializers.po_serializer import PurchaseOrderSerializer
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django.http import Http404
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from django.db.models import Q


class VendorListCreateAPIView(APIView):

    authentication_classes = [TokenAuthentication]  # Add token authentication
    permission_classes = [
        IsAuthenticated
    ]  # Add permission to only allow authenticated users

    def get(self, request):
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorDetailAPIView(APIView):

    authentication_classes = [TokenAuthentication]  # Add token authentication
    permission_classes = [
        IsAuthenticated
    ]  # Add permission to only allow authenticated users

    def get_object(self, vendor_id):
        try:
            return Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            return None

    def get(self, request, vendor_id):
        vendor = self.get_object(vendor_id)
        if vendor is not None:
            serializer = VendorSerializer(vendor)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, vendor_id):
        vendor = self.get_object(vendor_id)
        if vendor is not None:
            serializer = VendorSerializer(vendor, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, vendor_id):
        vendor = self.get_object(vendor_id)
        if vendor is not None:
            vendor.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND
            )


class PurchaseOrderListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]  # Add token authentication
    permission_classes = [
        IsAuthenticated
    ]  # Add permission to only allow authenticated users

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [SearchFilter]
    search_fields = ["vendor__name"]

    def perform_create(self, serializer):
        serializer.save()


class PurchaseOrderDetailAPIView(APIView):

    authentication_classes = [TokenAuthentication]  # Add token authentication
    permission_classes = [
        IsAuthenticated
    ]  # Add permission to only allow authenticated users

    def get(self, request, po_id, format=None):
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
            serializer = PurchaseOrderSerializer(purchase_order)
            return Response(serializer.data)
        except PurchaseOrder.DoesNotExist:
            raise Http404

    def put(self, request, po_id, format=None):
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
            serializer = PurchaseOrderSerializer(purchase_order, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PurchaseOrder.DoesNotExist:
            raise Http404

    def delete(self, request, po_id, format=None):
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
            purchase_order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PurchaseOrder.DoesNotExist:
            raise Http404


class VendorPerformanceAPIView(APIView):
    authentication_classes = [TokenAuthentication]  # Add token authentication
    permission_classes = [
        IsAuthenticated
    ]  # Add permission to only allow authenticated users

    def get(self, request, vendor_id):
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
            performance_metrics = self.calculate_performance_metrics(vendor)
            serializer = HistoricalPerformanceSerializer(performance_metrics)
            return Response(serializer.data)
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

    def calculate_performance_metrics(self, vendor):
        current_date = timezone.now()

        total_pos = PurchaseOrder.objects.filter(vendor=vendor).count()

        completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status="completed")

        total_completed_pos = completed_pos.count()

        on_time_pos = PurchaseOrder.objects.filter(
            issue_date__lte=F("delivery_date"), status="completed", vendor=vendor
        )

        total_on_time_pos = on_time_pos.count()

        # Calculate on-time delivery rate and fulfillment rate if total_completed_pos > 0
        if total_completed_pos > 0:
            on_time_delivery_rate = (total_on_time_pos / total_completed_pos) * 100
            fulfillment_rate = (total_completed_pos / total_pos) * 100

        # Calculate quality rating average
        quality_rating_avg = (
            completed_pos.aggregate(average_quality_rating=Avg("quality_rating"))[
                "average_quality_rating"
            ]
            or 0
        )

        # Round the quality_rating_avg to one decimal place
        quality_rating_avg_rounded = round(quality_rating_avg, 1)

        # Calculate average response time in hours
        average_response_time = (
            completed_pos.aggregate(
                average_response_time=Avg(
                    ExpressionWrapper(
                        F("acknowledgment_date") - F("issue_date"),
                        output_field=DurationField(),
                    )
                )
            )["average_response_time"]
            or timedelta(seconds=0)
        ).total_seconds() / 3600  # Convert seconds to hours

        performance_metrics_data = {
            "vendor": vendor,
            "date": current_date,
            "on_time_delivery_rate": on_time_delivery_rate,
            "quality_rating_avg": quality_rating_avg_rounded,
            "average_response_time": average_response_time,
            "fulfillment_rate": fulfillment_rate,
        }

        return HistoricalPerformance.objects.create(**performance_metrics_data)


class ObtainAuthToken(APIView):

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if username is None or password is None:
            return Response(
                {"error": "Please provide both username and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
