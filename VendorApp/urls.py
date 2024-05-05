from django.urls import path
from .views import (
    ObtainAuthToken,
    PurchaseOrderDetailAPIView,
    PurchaseOrderListCreateAPIView,
    VendorDetailAPIView,
    VendorListCreateAPIView,
    VendorPerformanceAPIView,
)

urlpatterns = [
    path("api/vendors/", VendorListCreateAPIView.as_view(), name="vendor-list-create"),
    path(
        "api/vendors/<int:vendor_id>/",
        VendorDetailAPIView.as_view(),
        name="vendor_detail",
    ),
    path(
        "api/purchase_orders/",
        PurchaseOrderListCreateAPIView.as_view(),
        name="purchase_order_list_create",
    ),
    path(
        "api/purchase_orders/<int:po_id>/",
        PurchaseOrderDetailAPIView.as_view(),
        name="purchase_order_detail",
    ),
    path(
        "api/vendors/<int:vendor_id>/performance/",
        VendorPerformanceAPIView.as_view(),
        name="vendor_performance",
    ),
    path('token/', ObtainAuthToken.as_view(), name='api-token'),

]
