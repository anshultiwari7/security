from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Sum, Count
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request


from portfolio.models import Ticker, Trade
from portfolio.serializers import (TradeSerializer, TickerSerializer, 
    HoldingSerializer, ReturnSerializer)
# Create your views here.


class TradeViewSet(viewsets.ViewSet):
    
    """ 
    TradeViewSet class to implement HTTP request methods
    over Trade model
      
    Attributes: 
        serializer_class (TradeSerializer): TradeSerializer
        model (Trade): Trade model
    """
    serializer_class = TradeSerializer
    model = Trade

    def get_queryset(self):
        return self.model.objects.select_related('ticker')

    def list(self, request):

        """ 
        Generating trades & related data
      
        Returns: 
        html: 
            rendered HTML with trade-list & tickers/categories for select box
        """
        if _id := request.GET.get('ticker'):
            data = self.serializer_class(
                self.get_queryset().filter(ticker__id=_id), many=True).data
        else:
            data = self.serializer_class(self.get_queryset(), many=True).data
        return render(request, 'trade_list.html', { 
                'trade_list': data, 
                'tickers': Ticker.objects.all(), 
                'trades_by_category': self.serializer_class(
                    self.get_queryset().distinct('category'), many=True).data
            })

    def retrieve(self, request, pk=None):

        """ 
        Generating trade & related data
      
        Returns: 
        html: 
            rendered HTML with trade & tickers/categories for select box
        """
        trade = get_object_or_404(self.get_queryset(), pk=pk)
        context = { 
            'trade': trade, 
            'tickers': Ticker.objects.all(), 
            'trades_by_category': self.serializer_class(
                self.get_queryset().distinct('category'), many=True).data}
        return render(request, 'trade_add_or_update.html', context)

    def create(self, request):

        """ 
        Saving trade & related data
      
        Returns: 
        html: 
            rendered HTML with success/error template
        """
        serializer = self.serializer_class(data=request.data,
            context=self.request)
        if serializer.is_valid():
            serializer.save()
            return render(request, 'success.html', {})
        return render(request, 'error.html', 
            { 'errors' : serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        serializer = self.serializer_class(
            data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(pk, serializer.validated_data)
            return render(request, 'success.html', {})
        return render(request, 'error.html', 
            { 'errors' : serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_record(self, request, pk=None):

        """ 
        Updateing trade
      
        Returns: 
        html: 
            rendered HTML with success/error template
        """
        _instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(
            data=request.data)
        if serializer.is_valid():
            serializer.update(_instance, serializer.validated_data)
            return render(request, 'success.html', {})
        return render(request, 'error.html', 
            { 'errors' : serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def add_new(self, request):
        return render(request, 'trade_add_or_update.html', {
            'tickers': Ticker.objects.all(), 
            'trades_by_category': self.serializer_class(
                self.get_queryset().distinct('category'),
                many=True).data
        })


class TickerViewSet(viewsets.ViewSet):

    """
        A viewset to list, retreive, create & partial update ticker
    """
    serializer_class = TickerSerializer
    model = Ticker

    def get_queryset(self):
        return self.model.objects.prefetch_related('trade_set') \
            .annotate(trade_count=Count('trade__id'))

    def create(self, request):

        """ 
        Saving ticker & related data
      
        Returns: 
        html: 
            rendered HTML with success/error template
        """
        serializer = self.serializer_class(data=request.data,
            context=self.request)
        if serializer.is_valid():
            serializer.save()
            return render(request, 'success.html', {})
        return render(request, 'error.html', { 'errors' : serializer.errors },
            status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):

        """ 
        Generating tickers & related data
      
        Returns: 
        html: 
            rendered HTML with ticker-list
        """
        context = { 'ticker_list': self.serializer_class(
            self.get_queryset(), many=True).data }
        return render(request, 'ticker_list.html', context)

    def retrieve(self, request, pk=None):

        """ 
        Generating ticker & related data
      
        Returns: 
        html: 
            rendered HTML with ticker data
        """
        ticker = get_object_or_404(self.get_queryset(), pk=pk)
        return render(request, 'ticker_add_or_update.html', 
            {'ticker': self.serializer_class(ticker).data })

    @action(detail=True, methods=['post'])
    def update_record(self, request, pk=None):

        """ 
        Updateing ticker
      
        Returns: 
        html: 
            rendered HTML with success/error template
        """
        _instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(
            data=request.data)
        if serializer.is_valid():
            serializer.update(_instance, serializer.validated_data)
            return render(request, 'success.html', {}, 
                status=status.HTTP_201_CREATED)
        return render(request, 'error.html', 
            { 'errors' : serializer.errors }, status=status.HTTP_200_ACCEPTED)

    @action(detail=False, methods=['get'])
    def add_new(self, request):        
        return render(request, 'ticker_add_or_update.html', {})


class HoldingViewSet(viewsets.ViewSet):

    """ 
    HoldingViewSet class to implement HTTP request methods
    over Trade/Ticker models data
    Working for FinalQuantity & Avg. Buy Price specifically
    Attributes: 
        serializer_class (HoldingSerializer): HoldingSerializer
    """
    serializer_class = HoldingSerializer
    
    def get_queryset(self, evaluated):
        return Ticker.objects.holdings(evaluated=evaluated)

    def list(self, request):
        evaluated = bool(int(request.GET.get('evaluated', 1)))
        context = {
            'holding_list': self.serializer_class(
                self.get_queryset(evaluated), many=True).data, 
            'evaluated': evaluated
        }
        return render(request, 'holding_list.html', context)


class ReturnViewSet(viewsets.ViewSet):

    """ 
    ReturnViewSet class to implement HTTP request methods
    over Trade/Ticker models data
    Working for CumulativeReturn specifically
      
    Attributes: 
        serializer_class (HoldingSerializer): HoldingSerializer
    """
    serializer_class = ReturnSerializer

    def get_queryset(self):
        return Ticker.objects.returns()

    def list(self, request):
        context = { 'return_list': self.serializer_class(
            self.get_queryset(), many=True).data }
        return render(request, 'return_list.html', context)
