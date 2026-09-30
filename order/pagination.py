# pagination.py
from rest_framework.pagination import PageNumberPagination

class OrderPagination(PageNumberPagination):
    page_size = 10              # first load
    page_size_query_param = 'page_size'
    max_page_size = 50

