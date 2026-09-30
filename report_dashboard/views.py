from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from order.models import Order, OrderItem


class DashboardAPIView(APIView):

    def get(self, request):
        period = request.query_params.get("period", "daily")

        # --------------------------------
        # Use local timezone
        # --------------------------------
        now = timezone.localtime(timezone.now())

        # --------------------------------
        # Determine reporting period
        # --------------------------------
        if period == "daily":

            start = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        elif period == "weekly":

            # Monday 00:00 -> now
            start = (
                now - timedelta(days=now.weekday())
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        elif period == "monthly":

            # First day of current month -> now
            start = now.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        else:
            return Response(
                {
                    "error": (
                        "Invalid period. "
                        "Use daily, weekly, or monthly."
                    )
                },
                status=400,
            )

        # --------------------------------
        # Orders inside reporting period
        # --------------------------------
        orders = Order.objects.filter(
            created_at__gte=start,
            created_at__lt=now,
        )

        # --------------------------------
        # Debug
        # --------------------------------
        print("================================")
        print("PERIOD:", period)
        print("NOW:", now)
        print("START:", start)
        print("ORDER COUNT:", orders.count())
        print("================================")

        # ============================================================
        # REVENUE
        # ============================================================
        #
        # Order total:
        #
        # subtotal
        # + service fee
        # + delivery charge
        # - discount
        #
        # ============================================================

        item_revenue_expression = ExpressionWrapper(
            F("total_price") * F("quantity"),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        )

        # --------------------------------
        # Item subtotal
        # --------------------------------
        item_subtotal = (
            OrderItem.objects
            .filter(order__in=orders)
            .aggregate(
                total=Sum(item_revenue_expression)
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------
        # Service fees
        # --------------------------------
        service_fee_total = (
            orders.aggregate(
                total=Sum("service_fee")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------
        # Delivery charges
        # --------------------------------
        delivery_charge_total = (
            orders.aggregate(
                total=Sum("delivery_charge")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------
        # Discounts
        # --------------------------------
        discount_total = (
            orders.aggregate(
                total=Sum("discount")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------
        # FINAL REVENUE
        # --------------------------------
        total_revenue = (
            item_subtotal
            + service_fee_total
            + delivery_charge_total
            - discount_total
        )

        # Never allow negative revenue
        total_revenue = max(
            total_revenue,
            Decimal("0.00")
        )

        # ============================================================
        # KPI
        # ============================================================

        total_orders = orders.count()

        avg_order = (
            total_revenue / total_orders
            if total_orders
            else Decimal("0.00")
        )

        # ============================================================
        # DELIVERY VS COLLECTION
        # ============================================================

        delivery_count = orders.filter(
            order_type="delivery"
        ).count()

        collection_count = orders.filter(
            order_type__in=["collection", "pickup"]
        ).count()

        # ============================================================
        # TOP SELLING ITEMS
        # ============================================================

        top_items = (
            OrderItem.objects
            .filter(order__in=orders)
            .values("item__name")
            .annotate(
                sales=Sum("quantity")
            )
            .order_by("-sales")[:5]
        )

        top_items_data = [
            {
                "name": item["item__name"],
                "sales": item["sales"],
            }
            for item in top_items
        ]

        # ============================================================
        # PEAK HOURS
        # ============================================================

        peak_hours = (
            orders
            .annotate(
                hour=ExtractHour("created_at")
            )
            .values("hour")
            .annotate(
                count=Count("id")
            )
            .order_by("hour")
        )

        peak_hours_data = [
            {
                "hour": item["hour"],
                "count": item["count"],
            }
            for item in peak_hours
        ]

        # ============================================================
        # REVENUE TREND
        # ============================================================
        #
        # IMPORTANT:
        # Revenue trend must also include:
        #
        # items + service fee + delivery - discount
        #
        # ============================================================

        revenue_trend = []

        dates = (
            orders
            .annotate(
                date=TruncDate("created_at")
            )
            .values("date")
            .distinct()
            .order_by("date")
        )

        for date_item in dates:

            date = date_item["date"]

            daily_orders = orders.filter(
                created_at__date=date
            )

            # Item subtotal for this day
            daily_subtotal = (
                OrderItem.objects
                .filter(order__in=daily_orders)
                .aggregate(
                    total=Sum(item_revenue_expression)
                )["total"]
                or Decimal("0.00")
            )

            # Service fees
            daily_service_fee = (
                daily_orders.aggregate(
                    total=Sum("service_fee")
                )["total"]
                or Decimal("0.00")
            )

            # Delivery charges
            daily_delivery_charge = (
                daily_orders.aggregate(
                    total=Sum("delivery_charge")
                )["total"]
                or Decimal("0.00")
            )

            # Discounts
            daily_discount = (
                daily_orders.aggregate(
                    total=Sum("discount")
                )["total"]
                or Decimal("0.00")
            )

            daily_total = (
                daily_subtotal
                + daily_service_fee
                + daily_delivery_charge
                - daily_discount
            )

            daily_total = max(
                daily_total,
                Decimal("0.00")
            )

            revenue_trend.append({
                "date": date,
                "revenue": daily_total,
            })

        # --------------------------------
        # Trend data
        # --------------------------------

        trend_labels = [
            str(item["date"])
            for item in revenue_trend
        ]

        trend_data = [
            float(item["revenue"])
            for item in revenue_trend
        ]

        # ============================================================
        # RESPONSE
        # ============================================================

        return Response(
            {
                "period": period,

                "periodStart": start,

                "periodEnd": now,

                "kpi": {
                    "totalRevenue": float(
                        total_revenue
                    ),

                    "totalOrders": total_orders,

                    "avgOrder": round(
                        float(avg_order),
                        2,
                    ),

                    # Optional breakdown
                    "subtotal": float(
                        item_subtotal
                    ),

                    "serviceFee": float(
                        service_fee_total
                    ),

                    "deliveryCharge": float(
                        delivery_charge_total
                    ),

                    "discount": float(
                        discount_total
                    ),
                },

                "deliveryStats": {
                    "delivery": delivery_count,

                    "collection": collection_count,
                },

                "topItems": top_items_data,

                "peakHours": peak_hours_data,

                "revenueTrend": {
                    "labels": trend_labels,

                    "data": trend_data,
                },
            }
        )

