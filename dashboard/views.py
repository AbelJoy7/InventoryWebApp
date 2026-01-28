from decimal import Decimal
from tkinter import ROUND
from urllib import request
from django.shortcuts import render
from .models import Sales, purchase
from django.utils import timezone
from datetime import timedelta
import sqlite3
from django.db.models import Sum, Avg, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from collections import defaultdict
import json
from django.http import JsonResponse
from datetime import date


# Create your views here.
def home(request):
    return render(request, 'dashboard/home.html')

def dashboard(request):
    context = {}

    context['sales'] = Sales.objects.all()
    context['purchases'] = purchase.objects.all()

    context['last_date'] = (
        Sales.objects.latest('date').date
        if Sales.objects.exists()
        else None
    )

    period = request.GET.get('time_filter')

    if period:
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()

        # Date condition (shared)
        if period == 'last_day':
            date_condition = "date = DATE('now')"
        elif period == 'last_week':
            date_condition = "date >= DATE('now', '-7 days')"
        elif period == 'last_month':
            date_condition = "date >= DATE('now', '-1 month')"
        else:
            date_condition = "date >= DATE('now', '-1 year')"

        # ---- SALES QUERY ----
        sales_query = f"""
        SELECT 
            SUM(quantity),
            AVG(price),
            SUM(quantity * price)
        FROM dashboard_sales
        WHERE {date_condition}
        """

        cursor.execute(sales_query)
        s_qty, s_avg, s_total = cursor.fetchone()

        context['sales_filtered'] = {
            'total_quantity': s_qty or 0,
            'average_price': round(s_avg or 0, 2),
            'total_amount': s_total or 0
        }

        # ---- PURCHASE QUERY ----
        purchase_query = f"""
        SELECT 
            SUM(quantity),
            AVG(price),
            SUM(quantity * price)
        FROM dashboard_purchase
        WHERE {date_condition}
        """

        cursor.execute(purchase_query)
        p_qty, p_avg, p_total = cursor.fetchone()

        context['purchases_filtered'] = {
            'total_quantity': p_qty or 0,
            'average_price': round(p_avg or 0, 2),
            'total_amount': p_total or 0
        }

        conn.close()

    purchase_data_monthly = (
        context['purchases']
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_purchase_quantity=Sum('quantity'),
            avg_purchase_price=Avg('price'),
            total_purchase_amount=Sum(
                ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
            )
        )
        .order_by('month')
    )
    sales_data_monthly = (
        context['sales']
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_sales_quantity=Sum('quantity'),
            avg_sales_price=Avg('price'),
            total_sales_amount=Sum(
                ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
            )
        )
        .order_by('month')
    )


    monthly_report = defaultdict(dict)

    for p in purchase_data_monthly:
        month = p['month']
        monthly_report[month].update(p)

    for s in sales_data_monthly:
            month = s['month']
            monthly_report[month].update(s)

    context['monthly_report'] = [
        {
            'month': month,
            'total_purchase_quantity': data.get('total_purchase_quantity', 0),
            'total_sales_quantity': data.get('total_sales_quantity', 0),
            'avg_purchase_price': round(data.get('avg_purchase_price', 0), 2),
            'avg_sales_price': round(data.get('avg_sales_price', 0), 2),
            'total_purchase_amount': data.get('total_purchase_amount', 0),
            'total_sales_amount': data.get('total_sales_amount', 0),
        }
        for month, data in sorted(monthly_report.items(), reverse=True)
    ]



  


    return render(request, 'dashboard/dashboard.html', context)



def sales_entry(request):
    if request.method == 'POST':
        date = request.POST['date']
        product = request.POST['product']
        quantity = request.POST['quantity']
        price = request.POST['price']
        total = float(quantity) * float(price)

        sales_record = Sales(date=date, product=product, quantity=quantity, price=price, sales_total=total)
        sales_record.save()

        # Save to database here

    return render(request, 'sales/sales_entry.html')

def purchase_entry(request):
    if request.method == 'POST':
        date = request.POST['date']
        item = request.POST['item']
        quantity = int(request.POST.get("quantity"))
        price = Decimal(request.POST.get("price"))
        seller_name = request.POST['seller_name']
        seller_place = request.POST['seller_place']
        seller_phno = request.POST['seller_phno']

        total = quantity * price

        # Save to DB here
        purchase_record = purchase(date=date, item=item, quantity=quantity, price=price, seller_name=seller_name, seller_place=seller_place, seller_phno=seller_phno, purchase_total=total)
        purchase_record.save()

    return render(request, 'purchase/purchase_entry.html')


def product_dashboard(request):
    context = {}

    # Base querysets
    sales_qs = Sales.objects.all()
    purchase_qs = purchase.objects.all()

    # For dropdown
    context['products'] = purchase.objects.values_list('item', flat=True).distinct()
    context['products'] = context['products'].union(
        Sales.objects.values_list('product', flat=True).distinct()
    )
    

    selected_product = None

    if request.method == 'POST':
        selected_product = request.POST.get('product_select')
        context['selected_product'] = selected_product

        # ✅ FILTER BY SELECTED PRODUCT
        if selected_product:
            purchase_qs = purchase_qs.filter(item=selected_product)
            sales_qs = sales_qs.filter(product=selected_product)

    # ✅ MONTHLY PURCHASE DATA (AFTER FILTER)
    purchase_data_monthly = (
        purchase_qs
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_purchase_quantity=Sum('quantity'),
            avg_purchase_price=Avg('price'),
            total_purchase_amount=Sum(
                ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
            )
        )
        .order_by('month')
    )

    # ✅ MONTHLY SALES DATA (AFTER FILTER)
    sales_data_monthly = (
        sales_qs
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_sales_quantity=Sum('quantity'),
            avg_sales_price=Avg('price'),
            total_sales_amount=Sum(
                ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
            )
        )
        .order_by('month')
    )

    # ✅ MERGE BOTH
    monthly_report = defaultdict(dict)

    for p in purchase_data_monthly:
        monthly_report[p['month']].update(p)

    for s in sales_data_monthly:
        monthly_report[s['month']].update(s)

    context['monthly_report'] = [
        {
            'month': month,
            'total_purchase_quantity': data.get('total_purchase_quantity', 0),
            'total_sales_quantity': data.get('total_sales_quantity', 0),
            'avg_purchase_price': round(data.get('avg_purchase_price', 0), 2),
            'avg_sales_price': round(data.get('avg_sales_price', 0), 2),
            'total_purchase_amount': data.get('total_purchase_amount', 0),
            'total_sales_amount': data.get('total_sales_amount', 0),
        }
        for month, data in sorted(monthly_report.items(), reverse=True)
    ]

    return render(request, 'dashboard/products.html', context)






from django.views.decorators.csrf import csrf_exempt    
@csrf_exempt   # only for development
def chatbot(request):

    # ✅ Step 1: If someone opens URL in browser (GET)
    if request.method == "GET":
        return JsonResponse({
            "reply": "Chatbot is running. Please send POST request with message."
        })

    # ✅ Step 2: Only read JSON for POST
    if request.method == "POST":

        # safety check
        if not request.body:
            return JsonResponse({"reply": "Request body is empty"}, status=400)

        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"reply": "Invalid JSON"}, status=400)

        msg = data.get("message", "").lower()

        if "today" in msg and "sale" in msg:
            total = Sales.objects.filter(date=date.today()).count()
            return JsonResponse({"reply": f"Today's total sales: {total}"})

        elif "low stock" in msg:
            items = purchase.objects.filter(stock__lt=10).count()
            return JsonResponse({"reply": f"{items} products are low in stock."})

        elif "today" in msg and "total purchase" in msg:
            total_purchase = purchase.objects.aggregate(
                total_amount=Sum(
                    ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
                )
            )['total_amount'] or 0
            return JsonResponse({"reply": f"Total purchase amount is: {total_purchase}"})

        else:
            return JsonResponse({"reply": "Sorry, I didn't understand."})

    return JsonResponse({"reply": "Method not allowed"}, status=405)

def chatbox_page(request):
    return render(request, "dashboard/chatpage.html")


