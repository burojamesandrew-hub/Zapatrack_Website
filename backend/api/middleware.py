"""
API Exception Middleware
Catches all exceptions from API routes and returns JSON instead of HTML.
"""
from django.http import JsonResponse
from rest_framework import status as drf_status
import json


class APIExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            if request.path.startswith('/api/'):
                print(f'[API Middleware] Exception in {request.path}: {e}')
                import traceback
                traceback.print_exc()
                return JsonResponse(
                    {'error': f'Server error: {str(e)}'},
                    status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            raise
