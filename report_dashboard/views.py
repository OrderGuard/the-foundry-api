from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from order.models import Order, OrderItem


class DashboardAPIView(APIView):

    def get(self, request):
        period = request.query_params.get("period", "daily")

        # ============================================================
        # USE LOCAL TIMEZONE
        # ============================================================

        now = timezone.localtime(timezone.now())

        # ============================================================
        # DETERMINE REPORTING PERIOD
        # ============================================================

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

        # ============================================================
        # ORDERS INSIDE REPORTING PERIOD
        # ============================================================

        orders = Order.objects.filter(
            created_at__gte=start,
            created_at__lt=now,
        )

        # ============================================================
        # DEBUG
        # ============================================================

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
        # IMPORTANT:
        #
        # OrderItem.total_price is already the LINE TOTAL.
        #
        # Example:
        #
        # item_price = £11.50
        # quantity   = 2
        # total_price = £23.00
        #
        # Therefore:
        #
        # DO NOT do:
        #
        # total_price * quantity
        #
        # because that would become:
        #
        # £23 × 2 = £46  ❌
        #
        # Instead:
        #
        # Sum(total_price) = £23  ✅
        #
        # ============================================================

        item_subtotal = (
            OrderItem.objects
            .filter(order__in=orders)
            .aggregate(
                total=Sum("total_price")
            )["total"]
            or Decimal("0.00")
        )

        # ============================================================
        # SERVICE FEES
        # ============================================================

        service_fee_total = (
            orders.aggregate(
                total=Sum("service_fee")
            )["total"]
            or Decimal("0.00")
        )

        # ============================================================
        # DELIVERY CHARGES
        # ============================================================

        delivery_charge_total = (
            orders.aggregate(
                total=Sum("delivery_charge")
            )["total"]
            or Decimal("0.00")
        )

        # ============================================================
        # DISCOUNTS
        # ============================================================

        discount_total = (
            orders.aggregate(
                total=Sum("discount")
            )["total"]
            or Decimal("0.00")
        )

        # ============================================================
        # FINAL REVENUE
        # ============================================================
        #
        # subtotal
        # + service fee
        # + delivery charge
        # - discount
        #
        # Example:
        #
        # £23.00
        # + £0.75
        # + £0.00
        # - £5.75
        # ----------
        # £18.00
        #
        # ============================================================

        total_revenue = (
            item_subtotal
            + service_fee_total
            + delivery_charge_total
            - discount_total
        )

        # Never allow negative revenue
        total_revenue = max(
            total_revenue,
            Decimal("0.00"),
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
        # For each date:
        #
        # item subtotal
        # + service fee
        # + delivery charge
        # - discount
        #
        # IMPORTANT:
        # total_price is already the line total.
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

            # Orders for this date
            daily_orders = orders.filter(
                created_at__date=date
            )

            # --------------------------------------------------------
            # Daily item subtotal
            # --------------------------------------------------------
            #
            # DO NOT multiply total_price by quantity.
            #
            # total_price is already:
            #
            # unit price × quantity
            #
            daily_subtotal = (
                OrderItem.objects
                .filter(order__in=daily_orders)
                .aggregate(
                    total=Sum("total_price")
                )["total"]
                or Decimal("0.00")
            )

            # --------------------------------------------------------
            # Daily service fee
            # --------------------------------------------------------

            daily_service_fee = (
                daily_orders.aggregate(
                    total=Sum("service_fee")
                )["total"]
                or Decimal("0.00")
            )

            # --------------------------------------------------------
            # Daily delivery charge
            # --------------------------------------------------------

            daily_delivery_charge = (
                daily_orders.aggregate(
                    total=Sum("delivery_charge")
                )["total"]
                or Decimal("0.00")
            )

            # --------------------------------------------------------
            # Daily discount
            # --------------------------------------------------------

            daily_discount = (
                daily_orders.aggregate(
                    total=Sum("discount")
                )["total"]
                or Decimal("0.00")
            )

            # --------------------------------------------------------
            # Daily final revenue
            # --------------------------------------------------------

            daily_total = (
                daily_subtotal
                + daily_service_fee
                + daily_delivery_charge
                - daily_discount
            )

            # Never allow negative revenue
            daily_total = max(
                daily_total,
                Decimal("0.00"),
            )

            revenue_trend.append(
                {
                    "date": date,
                    "revenue": daily_total,
                }
            )

        # ============================================================
        # TREND DATA
        # ============================================================

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

