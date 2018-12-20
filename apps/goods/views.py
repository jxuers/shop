from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import *
from .serializer import *

# class GoodsListView(APIView):
#     """
#     商品列表页接口
#     """
#     def get(self, request):
#         # 查询商品列表接口
#         goods = Goods.objects.all()[:10]
#         serializer = GoodsModelSerializer(instance=goods, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         # 添加商品接口
#         # 如何使用serializer进行数据的验证功能？
#         serializer = GoodsModelSerializer(data=request.data)
#         if serializer.is_valid():
#             # 如果数据验证成功，将数据保存到数据库中
#             serializer.save()
#             # 数据保存成功，将当前添加的数据返回给前端
#             return Response(serializer.data)
#         return Response(serializer.errors)

class GoodsListPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'size'
    page_query_param = 'page'
    max_page_size = 12

from django_filters.rest_framework import DjangoFilterBackend
from .filter import GoodsListFilter
from rest_framework import filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


# 缓存：一般只对不经常变化的GET请求的数据进行缓存，而POST/UPDATE/DELETE这些请求是不需要缓存的。
# 缓存时间：如果在缓存期内，对不经常变化的数据进行了修改，这样的话是无法在前端页面显示这个新增的数据。所以这个缓存时间要灵活的设置。如果缓存过期，重新去服务器请求就可以了，没有过期直接从缓存中读取，不用再去服务器请求了。
# 缓存的优势：1. 增加前端数据的显示效率；2. 减轻服务器的压力；
# drf-extensions: 这个drf的缓存包使用的是内存缓存(LocalMomery)，一旦项目重启，内存中的缓存就清空了，然后重新去服务器请求并缓存。

class GoodsListView(mixins.ListModelMixin, mixins.RetrieveModelMixin,  viewsets.GenericViewSet):
    """

        商品列list:表页接口：该接口默认获取第一页的12条数据，并且支持过滤参数；
    retrieve:
        商品详情数据接口：需要传递商品ID；
    """
    # urls.py GoodsListView.as_view({'get': 'list', 'post':'create'})
    # mixins.ListModelMixin: 内部实现了list()函数
    # viewsets.GenericViewSet：实现了请求方法和函数的映射{'get': 'list', 'post':'create'}
    pagination_class = GoodsListPagination
    queryset = Goods.objects.all()
    # 使用TokenAuthentication这个类可以验证用户当前是否登录，如果在发送请求的时候，请求头中含有Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b说明当前用户已经登录，如果请求头中没有这个Token，说明用户没有登录。
    authentication_classes = []

    # 只通过authentication_classes就能够获知当前用户是否登录，但是当前这个接口是登录之后才能访问还是没有登录就能访问，就需要设置权限(默认AllowAny)。
    # 权限：1. 是否登录；2. 用户的类型；(用户登录的前提下)
    permission_classes = []

    serializer_class = GoodsModelSerializer
    # 设置过滤类
    # DjangoFilterBackend: 精确过滤数据，前端要搜索的数据必须和数据库中的值完全一致。比如：name='苹果' 搜索关键字必须是 "苹果"
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    # 使用内置的精确匹配
    # filter_fields：设置根据什么字段过滤(商品名称、商品的简介、商品的详情)
    # filter_fields = ('name', 'goods_brief')

    # DjangoFilterBackend无法满足模糊搜索，如果要实现模糊搜索(商品搜索、价格区间)
    # 此时需要自定义过滤器

    # 配置自定义的模糊过滤类(注意：filter_backends不能注释，因为它是过滤的核心组件。)
    filterset_class = GoodsListFilter

    # 总结：DjangoFilterBackend虽然可以实现模糊搜索，但是像商品的全局搜索一般不使用这个类，一般使用SearchFilter()。
    # 配置SearchFilter，这个类默认就是模糊搜索。
    search_fields = ('name', 'goods_brief')

    # OrdingFilter()用来做排序的类
    ordering_fields = ('sold_num', 'shop_price', 'add_time')
    # 如果前端没有传?ording参数，指定一个默认的排序方式
    ordering = ('-add_time', )

    # 商品的排序、搜索、过滤等功能：
    # 比如前端点击 "价格" 排序按钮，就会向后台接口发送请求，后台接口接收到这个请求之后，就会按照价格对商品进行排序，然后将排序之后的商品返回给前端，前端进行展示。
    # 比如前端输入了一个商品的价格区间，在点击查询按钮之后，前端会向后台接口发送请求，并将价格区间的值传递给后台，后台接口会根据这个价格区间去商品表中查询数据，并将查询结果返回给前端，前端再进行展示。
    # def get_queryset(self):
    #     # 重写get_queryset，默认情况下这个内置函数是获取所有数据了，但是前端需要对价格进行区间的过滤。
    #     # 先获取前端传递的价格区间
    #     # return Goods.objects.all().order_by('-shop_price')
    #     price_min = self.request.query_params.get('price_min', 0)
    #     price_max = self.request.query_params.get('price_max', 0)
    #     result = Goods.objects.all().filter(shop_price__gte=int(price_min), shop_price__lte=int(price_max))
    #     # 这个结果集交给self.filter_queryset(self.get_queryset())
    #     return result
    #     # 这种重写方式只适合单一的过滤/排序/查询，如果组合起来使用的话就无法满足需要了。

# 设计商品类别接口：
# 1. 导航条上以及全局商品搜索使用同一个接口：这两块内容都需要返回商品的所有类别数据(一级、二级、三级)；
# 2. 如果访问的是某一个一级类别下的数据：只需要返回二级类别和三级类别。

from rest_framework_extensions.cache.mixins import CacheResponseMixin


class GoodsCategoryView(CacheResponseMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    # mixins.RetrieveModelMixin: 获取某一个Model对象的所有数据(查询商品的详情) /ID/
    """
    所有商品类别接口
    """
    # ORM操作有惰性查询的特点：all()、filter()操作是没有查询数据库的，只是利用ORM生成了一个QuerySet对象，真正查询数据库是在使用这些对象时(比如：遍历)
    # 只使用GoodsCategorySerializer序列化1级类目，在对一级类目进行序列化的同时，GoodsCategorySerializer内部自动去序列化了二级目录，二级目录又自动序列化了三级目录
    queryset = GoodsCategory.objects.filter(category_type=1)
    serializer_class = GoodsCategorySerializer
    authentication_classes = []

    # 只通过authentication_classes就能够获知当前用户是否登录，但是当前这个接口是登录之后才能访问还是没有登录就能访问，就需要设置权限(默认AllowAny)。
    # 权限：1. 是否登录；2. 用户的类型；(用户登录的前提下)
    permission_classes = []

