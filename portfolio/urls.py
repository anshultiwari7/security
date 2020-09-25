from rest_framework.routers import DefaultRouter

from portfolio.views import (TickerViewSet, TradeViewSet, 
	HoldingViewSet, ReturnViewSet)

router = DefaultRouter()
router.register(r'ticker', TickerViewSet, basename='ticker')
router.register(r'trade', TradeViewSet, basename='trade')
router.register(r'holding', HoldingViewSet, basename='holding')
router.register(r'return', ReturnViewSet, basename='return')
urlpatterns = router.urls