from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Account, Destination
from .serializers import AccountSerializer, DestinationSerializer
import requests
from django.http import JsonResponse

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return self.queryset.filter(account_id=account_id)

    @action(detail=False, methods=['get'], url_path='account/(?P<account_id>[^/.]+)')
    def get_destinations(self, request, account_id=None):
        destinations = self.get_queryset()
        serializer = self.get_serializer(destinations, many=True)
        return Response(serializer.data)

def incoming_data(request):
    if request.method == 'POST':
        app_secret_token = request.headers.get('CL-X-TOKEN')
        if not app_secret_token:
            return JsonResponse({"message": "Un Authenticate"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            data = request.body.decode('utf-8')
            json_data = json.loads(data)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid Data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Account.objects.get(app_secret_token=app_secret_token)
            for destination in account.destinations.all():
                if destination.http_method.upper() == 'GET':
                    response = requests.get(destination.url, params=json_data, headers=destination.headers)
                elif destination.http_method.upper() in ['POST', 'PUT']:
                    response = requests.request(destination.http_method.upper(), destination.url, json=json_data, headers=destination.headers)
        
            return JsonResponse({"message": "Data sent to destinations"}, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return JsonResponse({"message": "Invalid Token"}, status=status.HTTP_403_FORBIDDEN)

    return JsonResponse({"message": "Invalid Method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

