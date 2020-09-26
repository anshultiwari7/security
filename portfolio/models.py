from django.db import models
from django.db.models.functions import Concat, Coalesce
from django.contrib import messages
from django.contrib.auth.models import AbstractUser, Permission
from django.core.validators import (MaxValueValidator, MinValueValidator)
from django.core.exceptions import ValidationError

# Create your models here.

"""
    Constant refering to current price of a security/ticker
        CURRENT_PRICE: Decimal
"""
CURRENT_PRICE = 100


class CreateModifyModel(models.Model):

    """
    Abstract Base model for attaching model attribute(s) -
        created_at
        modified_at
    """
    created_at = models.DateTimeField(auto_now_add=True, editable=True)
    modified_at = models.DateTimeField(auto_now=True, editable=True)

    class Meta:
        abstract = True


class SoftDeleteCreateModifyModel(CreateModifyModel):

    """
    Abstract Base model for attaching model attribute(s) -
        active
    """
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TickerManager(models.Manager):

    """
        ManagerMethod: 
            holdings
            returns
    """
    def holdings(self, evaluated=True):

        """ 
        Holdings method computing ticker details, final_quantity & 
        avg_buy_price of their trades
      
        Parameters: 
        evaluated (bool): evaluated True sets avg_buy_price computed
        result of calculation string otherwise not
      
        Returns: 
        list: List of holdings having ticker details - id, name, symbol
        avg_buy_price, final_quantity
        """
        queryset = Ticker.objects.all().prefetch_related('trade_set') \
            .values('id', 'name', 'symbol', 'trade__price', 'trade__category') \
            .order_by('trade__price') \
            .annotate(final_quantity=Coalesce(models.Sum('trade__quantity'), 0))
        holdings_data = []
        holdings = {}
        for qs in queryset:
            try:
                if qs.get('trade__category') == Trade.CATEGORY_BOUGHT:
                    if holdings[qs.get('id')].get('avg_buy_price'):
                        holdings[qs.get('id')]['avg_buy_price'] = ' + '.join([ 
                            holdings[qs.get('id')]['avg_buy_price'],
                            '*'.join([str(qs.get('trade__price')),
                            str(qs.get('final_quantity'))])]
                        )
                        holdings[qs.get('id')]['divider'] = ' + '.join([
                            holdings[qs.get('id')]['divider'],
                            str(qs.get('final_quantity'))]
                        )
                        holdings[qs.get('id')]['bought'] += qs.get('final_quantity')
                    else:
                        holdings[qs.get('id')]['avg_buy_price'] = ' + '.join([
                            '*'.join([str(qs.get('trade__price')),
                            str(qs.get('final_quantity'))])]
                        )
                        holdings[qs.get('id')]['divider'] = str(qs.get('final_quantity'))
                        holdings[qs.get('id')]['bought'] = qs.get('final_quantity')
                if qs.get('trade__category') == Trade.CATEGORY_SOLD:
                    try:
                        holdings[qs.get('id')]['sold'] += qs.get('final_quantity')
                    except:
                        holdings[qs.get('id')]['sold'] = qs.get('final_quantity')
                holdings[qs.get('id')]['id'] = qs.get('name')
                holdings[qs.get('id')]['name'] = qs.get('name')
                holdings[qs.get('id')]['symbol'] = qs.get('symbol')
                holdings[qs.get('id')]['final_quantity'] += qs.get('final_quantity')
            except:
                holdings[qs.get('id')] = {}
                holdings[qs.get('id')]['id'] = qs.get('name')
                holdings[qs.get('id')]['name'] = qs.get('name')
                holdings[qs.get('id')]['final_quantity'] = qs.get('final_quantity')
                holdings[qs.get('id')]['avg_buy_price'] = 0
                holdings[qs.get('id')]['divider'] = ''
                if (qs.get('trade__price') or (qs.get('trade__price') == 0) and 
                        qs.get('trade__category') == Trade.CATEGORY_BOUGHT):
                    holdings[qs.get('id')]['avg_buy_price'] = ' + '.join([
                        '*'.join([str(qs.get('trade__price')), 
                        str(qs.get('final_quantity'))])]
                    )
                    holdings[qs.get('id')]['divider'] = str(qs.get('final_quantity'))
                    holdings[qs.get('id')]['bought'] = qs.get('final_quantity')
                if qs.get('trade__category') == Trade.CATEGORY_SOLD:
                    holdings[qs.get('id')]['sold'] = qs.get('final_quantity')
                holdings[qs.get('id')]['id'] = qs.get('name')
                holdings[qs.get('id')]['name'] = qs.get('name')
                holdings[qs.get('id')]['symbol'] = qs.get('symbol')
        for k, v in holdings.items():
            if v.get('divider'):
                v['avg_buy_price'] = '/'.join([
                    ''.join(['(', v['avg_buy_price'], ')']), 
                    ''.join(['(', v['divider'], ')'])
                ])
            if evaluated:
                v['avg_buy_price'] = '%.2f'%eval(str(v['avg_buy_price']))
            if isinstance(v['avg_buy_price'], int):
                v['avg_buy_price'] = '%.2f'%v['avg_buy_price']
            v['final_quantity'] = (v.get('bought') or 0) - (v.get('sold') or 0)
            holdings_data.append(v)
        return holdings_data


    def returns(self):

        """ 
        Returns method computing ticker details & cumulative return
      
        Returns: 
        list: List of returns having ticker details - id, name, symbol
        avg_buy_price, final_quantity, cumulative_return
        """
        holdings = self.model.objects.holdings()
        returns_data = []
        for holding in holdings:
            returns_data.append({
                    'name': holding.get('name'),
                    'symbol': holding.get('symbol'),
                    'cumulative_return': '%.2f'%((CURRENT_PRICE - \
                        float(holding.get('avg_buy_price'))) * \
                        float(holding.get('final_quantity')) \
                        if holding.get('avg_buy_price') else 0)
                })
        return returns_data


class Ticker(SoftDeleteCreateModifyModel):

    """ 
    Ticker model for Ticker (Security) table
      
    Attributes: 
        id (int): Primary Key auto-increment & auto-generated
        name (int): Name of the ticker
        symbol (int): Symbol of the ticker
    """
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['symbol'], name='unique symbol')
            ]

    objects = TickerManager()


class TradeBase(SoftDeleteCreateModifyModel):

    """ 
    Abstract TradeBase model for Trade & TradeHistory model
      
    Attributes: 
        category (int): Integer for saving constant related to 
            bought/sold category
        quantity (int): Trade Quantity of ticker
        ticker (Ticker): Ticker instance foreign key
        price (decimal): Field representing traded price
    """
    CATEGORY_BOUGHT = 1
    CATEGORY_SOLD = 2
    CATEGORY_CHOICES = (
            (CATEGORY_BOUGHT, 'bought'),
            (CATEGORY_SOLD, 'sold')
        )
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    quantity = models.IntegerField(
        validators=[MaxValueValidator(9999999), MinValueValidator(1)])
    ticker = models.ForeignKey('portfolio.Ticker', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        abstract = True


class Trade(TradeBase):

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        TradeHistory.objects.create(
            trade_reference=self,
            category=self.category,
            quantity=self.quantity,
            ticker=self.ticker,
            price=self.price
        )


class TradeHistory(TradeBase):
    trade_reference = models.ForeignKey('portfolio.Trade', 
        on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ['-pk']
