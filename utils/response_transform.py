from rest_framework.response import Response
from rest_framework import status as http_status


def send_response(payload: dict, status_code: int = None) -> Response:
    """
    Transform and send a standardized API response.

    Args:
        payload (dict): The data to include in the response.
        status_code (int, optional): Override status code.

    Returns:
        Response: Django REST Framework response object.
    """
    # Default status
    final_status = http_status.HTTP_200_OK

    # If payload has 'status': 'error', use 400
    if payload.get("status") == "error":
        final_status = http_status.HTTP_400_BAD_REQUEST

    # Manual override
    if status_code is not None:
        final_status = status_code

    return Response(payload, status=final_status)

