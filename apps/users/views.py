from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import UserInfo

class CustomAuthenticate(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserInfo.objects.get(Q(username=username)|Q(mobile=username)|Q(email=username))
            if user.check_password(password):
                return user
        except Exception:
            return None

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from .serializer import *
from .models import *
import random
from utils.sms import YunPianSMSService
from django.conf import settings
from rest_framework import status
class SMSCodeView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    create:
        向用户手机发送验证码接口：前端需要将用户手机号传给这个接口，这个接口会对这个手机号进行验证，如果是正确的手机号，那么这个接口回向该手机号发送一个4位的验证码，同时将手机号验证码的发送JSON结果返回
    """
    # 用户发送验证码的接口类
    # 用户点击 "发送验证码" 按钮，前端会调用后台的接口，需要将用户在前端页面输入的手机号通过POST请求传递给后台接口，后台就会向这个手机号发送一个验证码，同时将这个验证码发送记录保存到数据库。
    serializer_class = SMSSerializer
    authentication_classes = []
    permission_classes = []

    def random_code(self):
        number = '0123456789'
        code = ''
        for x in range(4):
            code += random.choice(number)
        return code

    def create(self, request, *args, **kwargs):
        # 1. 获取序列化对象和对POST请求提交的数据进行验证
        serializer = self.get_serializer(data=request.data)
        # is_valid(raise_exception=True): 在对数据尽心验证的时候，如果有异常，直接将异常的响应返回给前端，is_valid之后的代码就不再执行了。
        serializer.is_valid(raise_exception=True)

        # 2. 获取请求中传递的手机号
        mobile = serializer.validated_data['mobile']
        # 先生成一个随机验证码
        code = self.random_code()

        # 3. 调用云片网发送短信的接口
        sms = YunPianSMSService(API_KEY=settings.API_KEY)
        result = sms.send_sms(mobile=mobile, code=code)

        # 将数据存储到数据库，在保存之前，先向用户手机号发送验证码
        if result['code'] == 0:
            # 表示验证码发送成功，然后就可以将这个code验证码和这个手机号绑定，保存到验证码记录表中。
            code_record = SMSVerifyCode(code=code, mobile=mobile)
            code_record.save()
            headers = self.get_success_headers(serializer.data)
            data = serializer.data
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            data = {
                'mobile': mobile,
                'code': result['code'],
                'msg': result['msg']
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler
class UserRegisterView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    # 用户注册接口类
    permission_classes = []
    authentication_classes = []
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = serializer.data

        # 生成JWT的Token
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        data['token'] = token

        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

class UserFavView(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    # 用户收藏接口类
    # CreateModelMixin(收藏): 在表中生成收藏记录
    # DestroyModelMixin(取消收藏): 将表中的收藏记录删除
    # ListModelMixin(会员中心-用户收藏): 获取当前登录用户的所有收藏记录
    # RetrieveModelMixin(是否收藏)：进入详情页的时候，需要查询某一条收藏记录是否存在
    queryset = UserFav.objects.all()


    # lookup_field一般作用于delete请求和retrieve请求(因为删除数据和查询详情数据都需要向后台接口传一个ID，这个ID的值默认使用的是pk的值，现在需要将pk换成商品ID，此时前端只需要将商品ID传给后台接口，就可以查询/删除这个收藏记录了)。
    lookup_field = 'goods_id'

    # 判断用户的操作是post创建还是get获取所有收藏列表
    def get_serializer_class(self):
        if self.action == 'list':
            # 获取所有收藏列表
            return UserFavListSerializer
        else:
            #
            return USerFavSerializer

    def get_queryset(self):
        # 重写get_queryset函数，默认是获取所有数据，但是收藏记录只需要获取登录用户的就行了。
        return UserFav.objects.filter(user=self.request.user)

# 获取用户信息：由于GenericViewSet和router.register()配合使用的时候，会自动注册api接口，这个接口严格按照restful api规范来注册的，所以前端调用接口的时候，必须遵循这个规范：
# http://localhost:8000/goods/
# GET: list获取所有商品；POST：添加商品
# http://localhost:8000/goods/id/
# GET: retrieve获取商品详情；DELETE：destroy删除某一个商品

# 但是获取某一个用户的详细信息，如果遵循API规范，必须http://localhost:8000/users/id/这样设置，但是此时的id又没有任何意义，只是为了符合API规范，对于后台查询用户数据而言没有任何作用。

# 所以，在获取用户详细信息时，不遵循API规范了(http://localhost:8000/users/)，不再使用router.register()注册API接口了。
class UserInfoView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    retrieve:
        获取用户详细信息接口。
    """
    serializer_class = UserInfoSerializer
    queryset = UserInfo.objects.all()

    def get_object(self):
        """
        这个方法就是RetrieveModelMixin中获取某一个数据的方法，内置的get_object()是根据pk也就是数据的id来获取某一个数据的，但是现在获取用户详细信息没有传递这个id，所以咱们需要重写这个get_object()方法。
        :return:
        """
        return self.request.user

# 用户留言：获取所有留言、添加留言、删除留言
class UserMessageView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    list:
        获取当前用户的所有留言信息接口
    """
    serializer_class = UserMessageSerializer
    def get_queryset(self):
        return UserLeavingMessage.objects.filter(user=self.request.user)

# 用户收货地址：增删改查都包含
class UserAddressView(viewsets.ModelViewSet):
    serializer_class = UserAddressSerializer
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
    # 在添加收获地址的时候，需要判断这个收货地址是否已经添加过了，如果已经存在就不能在添加了。
    def create(self, request, *args, **kwargs):
        address = UserAddress.objects.filter(province=request.data['province'], city=request.data['city'], district=request.data['district'], address=request.data['address'], signer_name=request.data['signer_name'], signer_mobile=request.data['signer_mobile'])
        if address:
            raise serializers.ValidationError('收货地址已存在')
        # 如果不存在，开始执行数据的序列化
        # POST执行序列化：将前端传递的参数字典序列化成为ORM对象，然后存储save()。
        # GET执行序列化：将数据库查询出来的ORM对象序列化成JSON字符串，然后返回给前端。
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = serializer.data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)



