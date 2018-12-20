from django.urls import path, include
from .views import *

from rest_framework.routers import DefaultRouter
# 这一套路由系统会根据GoodsListView接口所继承的类，自动生成对应的接口，比如：
router = DefaultRouter()
# 商品类别接口
router.register(r'categorys', GoodsCategoryView, base_name='categorys')
# 商品列表接口
router.register(r'', GoodsListView, base_name='list')

# /goods/categorys/
# /goods/categorys/<int:pk>/


urlpatterns = [
    path('', include(router.urls)),
]
