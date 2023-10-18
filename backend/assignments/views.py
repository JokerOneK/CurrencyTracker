from datetime import datetime, date, timedelta

from django.db import transaction
from django.db.models import Max, Min
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import AssignmentSerializer, CurrencyDataSerializer, \
    CurrencyHistorySerializer, AddUserCurrencySerializer
from .tasks import task_execute
from .models import Currency, UserCurrency, CurrencyData, Assignment


class AssignmentViewSet(viewsets.ModelViewSet):

    serializer_class = AssignmentSerializer
    queryset = Assignment.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                # save instance
                instance = serializer.save()
                instance.save()

                # create task params
                job_params = {"db_id": instance.id}

                # submit task for background execution
                transaction.on_commit(lambda: task_execute.delay(job_params))

        except Exception as e:
            raise APIException(str(e))


class AddUserCurrencyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = AddUserCurrencySerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            currency_id = serializer.validated_data['currency']
            threshold = serializer.validated_data['threshold']

            currency = get_object_or_404(Currency, pk=currency_id)

            user_currency, created = UserCurrency.objects.get_or_create(user=user, currency=currency, threshold = threshold)
            user_currency.save()

            response_data = {
                'message': f'{currency.char_code}  has been added to your watchlist with a threshold of {threshold}.'
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrencyDataAPIView(APIView):
    permission_classes = [AllowAny]  # Unregistered users can access this endpoint


    def get(self, request, order_by="value"):
        # Get today's date
        last_available_date = CurrencyData.objects.aggregate(Max('date'))['date__max']
        if request.query_params:
            order_by = request.query_params.get('order_by')

        if request.user.is_authenticated:
            # User is registered
            user = request.user

            # Retrieve currencies being tracked by the user
            tracked_currencies = UserCurrency.objects.filter(user=user)

            # Initialize a dictionary to store currency data with threshold check
            currency_data_with_threshold = {}

            for currency in tracked_currencies:
                # Retrieve currency data for today
                currency_data = CurrencyData.objects.filter(
                    currency=currency.currency,
                    date=last_available_date
                ).first()

                if currency_data:
                    # Calculate whether the price exceeds the threshold
                    price_exceeds_threshold = currency_data.price > currency.threshold

                    # Serialize the data and include the threshold check
                    serializer = CurrencyDataSerializer(currency_data)
                    serialized_data = serializer.data
                    serialized_data['exceeds_threshold'] = price_exceeds_threshold

                    currency_data_with_threshold[currency.currency.id] = serialized_data

            newIndex = sorted(currency_data_with_threshold, key=lambda x: currency_data_with_threshold[x]['price'])
            if order_by == "value":
                currency_data_with_threshold_sorted = {k: currency_data_with_threshold[k] for k in newIndex}
            else:
                currency_data_with_threshold_sorted = {k: currency_data_with_threshold[k] for k in reversed(newIndex)} # Bug

            return Response(currency_data_with_threshold_sorted, status=status.HTTP_200_OK)
        else:
            # User is unregistered, return all currency data for today
            currency_data = CurrencyData.objects.filter(date=last_available_date)
            if order_by == "value":
                currency_data = currency_data.order_by('price')
            else:
                currency_data = currency_data.order_by('-price')
            serializer = CurrencyDataSerializer(currency_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class CurrencyHistoryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, currency_id):
        # Get query parameters from the request
        # print(request.data)
        threshold = request.query_params.get('threshold')
        start_date = request.query_params.get('date_from')
        end_date = request.query_params.get('date_to')

        # Validate and parse query parameters
        serializer = CurrencyHistorySerializer(data={
            'currency_id': currency_id,
            'threshold': threshold,
            'start_date': start_date,
            'end_date': end_date,
        })

        if serializer.is_valid():
            threshold = serializer.validated_data['threshold']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']

            currency = get_object_or_404(Currency, pk=currency_id)
            char_code = currency.char_code

            # Retrieve currency data for the specified date range
            currency_data = CurrencyData.objects.filter(
                currency=currency,
                date__range=[start_date, end_date]
            ).order_by('date')

            data = []

            if currency_data.exists():
                # Calculate the minimum and maximum values
                min_price = currency_data.aggregate(min_price=Min('price'))['min_price']
                max_price = currency_data.aggregate(max_price=Max('price'))['max_price']

                for data_point in currency_data:
                    exceeds_threshold = data_point.price > threshold
                    is_minimum = data_point.price == min_price
                    is_maximum = data_point.price == max_price

                    # Calculate the percentage ratio between price and threshold
                    if threshold != 0:
                        price_threshold_ratio = str(round((data_point.price / threshold) * 100, 2)) + '%'
                    else:
                        price_threshold_ratio = None

                    # Determine the threshold match type
                    if data_point.price < threshold:
                        threshold_match_type = "less"
                    elif data_point.price == threshold:
                        threshold_match_type = "equal"
                    else:
                        threshold_match_type = "more"

                    data.append({
                        'id': currency_id,
                        'date': data_point.date,
                        'charcode': char_code,
                        'value': data_point.price,
                        'is_threshold_exceeded': exceeds_threshold,
                        'threshold_match_type': threshold_match_type,
                        'is_min_value': is_minimum,
                        'is_max_value': is_maximum,
                        'percentage_ratio': price_threshold_ratio,

                    })

            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
