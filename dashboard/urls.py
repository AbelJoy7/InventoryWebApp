from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard-home'),
    path('dashboard/', views.dashboard, name='dashboard-dashboard'),
    path('purchase_entry/', views.purchase_entry, name='purchase-purchase_entry'),
    path('sales_entry/', views.sales_entry, name='sales-sales_entry'),
    path('products/', views.product_dashboard, name='dashboard-products'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chat/', views.chatbox_page, name='chat'),
]