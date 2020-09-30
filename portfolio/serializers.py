from rest_framework import serializers
from django.db.models import Sum, Count
from portfolio.models import Ticker, Trade


class TickerSerializer(serializers.ModelSerializer):

    """ 
    TickerSerializer class to serializing Ticker model & calculating
    number_of_trades
    """
    id = serializers.ReadOnlyField()
    number_of_trades = serializers.SerializerMethodField(read_only=True)

    def get_number_of_trades(self, instance):
        return instance.trade_count

    class Meta:
        model = Ticker
        fields = ('id', 'name', 'symbol', 'number_of_trades')


class TradeSerializer(serializers.ModelSerializer):

    """ 
    TradeSerializer class to serializing TradeModel & related fields
    over Trade/Ticker models data
    Working for CumulativeReturn specifically
    """
    id = serializers.ReadOnlyField()
    ticker_id = serializers.IntegerField(write_only=True)
    ticker_name = serializers.SerializerMethodField(read_only=True)
    ticker_symbol = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Trade
        fields = (
            'id', 'category', 'ticker_id', 'quantity',
            'price', 'ticker_name', 'ticker_symbol', 'category_name'
        )

    def validate(self, data):
        data = super(TradeSerializer, self).validate(data)
        trades = Trade.objects.filter(
            ticker__id=data['ticker_id'])
        bought_qty = trades.filter(category=Trade.CATEGORY_BOUGHT).aggregate(
            bought_qty=Sum('quantity')).get('bought_qty') or 0
        sold_qty = trades.filter(category=Trade.CATEGORY_SOLD).aggregate(
            sold_qty=Sum('quantity')).get('sold_qty') or 0
        available_qty = bought_qty - sold_qty
        if data['category'] == Trade.CATEGORY_SOLD:
            if available_qty == 0:
                raise serializers.ValidationError({
                    'Quantity': 'No quantity available to sell'})
            if data['quantity'] > available_qty:
                raise serializers.ValidationError({
                    'Quantity': 'Available quantity to sell {available_qty}' \
                    .format(available_qty=available_qty)})
        return data

    def get_ticker_name(self, instance):
        return instance.ticker.name

    def get_ticker_symbol(self, instance):
        return instance.ticker.symbol

    def get_category_name(self, instance):
        return Trade.CATEGORY_CHOICES[instance.category-1][1]


class HoldingSerializer(serializers.ModelSerializer):

    """ 
    HoldingSerializer class to serializing ticker model &
    calculated values for avg_buy_price, final_quantity
    """
    id = serializers.ReadOnlyField()
    avg_buy_price = serializers.SerializerMethodField(read_only=True)
    final_quantity = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticker
        fields = (
            'id', 'name', 'symbol', 
            'final_quantity', 'avg_buy_price'
        )

    def get_avg_buy_price(self, instance):
        return instance.get('avg_buy_price')

    def get_final_quantity(self, instance):
        return instance.get('final_quantity')


class ReturnSerializer(serializers.ModelSerializer):
    
    """ 
    ReturnSerializer class to serializing ticker models &
    calculated values for cumulative_return
    """
    id = serializers.ReadOnlyField()
    cumulative_return = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticker
        fields = (
            'id', 'name', 'symbol', 
            'cumulative_return'
        )

    def get_cumulative_return(self, instance):
        return instance.get('cumulative_return')

