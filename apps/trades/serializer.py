from rest_framework import serializers
from .models import *
from goods.serializer import GoodsModelSerializer

class TradesCartListSerializer(serializers.ModelSerializer):
    # 在POST创建购物车记录的时候，需要保存用户
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # 前端需要将添加购物车的商品数量传到接口，需要保存到数据库中
    nums = serializers.IntegerField(required=True, min_value=1, error_messages={
        'required': '请选择购买数量',
        'min_value': '商品数量必须大于等于1'
    })
    goods = GoodsModelSerializer()
    class Meta:
        model = ShoppingCart
        fields = ('user', 'nums', 'goods', 'id')

class TradesCartSerializer(serializers.ModelSerializer):
    # 在POST创建购物车记录的时候，需要保存用户
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # 前端需要将添加购物车的商品数量传到接口，需要保存到数据库中
    nums = serializers.IntegerField(required=True, min_value=1, error_messages={
        'required': '请选择购买数量',
        'min_value': '商品数量必须大于等于1'
    })
    class Meta:
        model = ShoppingCart
        fields = ('user', 'nums', 'goods', 'id')

    def create(self, validated_data):
        # 获取当前登录用户
        user = self.context['request'].user
        # 获取经过后台is_valid()验证之后的前端数据。
        nums = validated_data['nums']
        goods = validated_data['goods']
        # 利用user和goods去数据库中查询这个用户的这个商品是否已经加入购物车
        records = ShoppingCart.objects.filter(user=user, goods=goods)
        if records:
            # 说明这个用户添加购物车的这个商品已经添加过了
            record = records[0]
            record.nums += nums
            record.save()
        else:
            record = ShoppingCart.objects.create(**validated_data)
        return record

class OrderGoodsSerializer(serializers.ModelSerializer):
    # 将OrderGoods表中的goods_id序列化成商品信息。
    goods = GoodsModelSerializer(many=False)
    class Meta:
        model = OrderGoods
        fields = "__all__"

from utils.alipay import AliPay
from restfulshop import settings
class TradesOrderSerializer(serializers.ModelSerializer):
    # 在发送POST的请求的时候，需要获取订单号，但是交易号、支付时间、订单状态不能写入
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    add_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    trade_no = serializers.CharField(read_only=True)
    pay_status = serializers.CharField(read_only=True)
    pay_time = serializers.DateTimeField(read_only=True)
    # 订单号也不允许前端提交，前端只提交订单的基本信息
    order_sn = serializers.CharField(read_only=True)

    # 以上是对订单的基本信息进行序列化，但是在进入订单详情页的时候，还需要商品的数据，需要对商品也进行序列化。
    goods = OrderGoodsSerializer(many=True, read_only=True)

    # 当前端点击结算按钮，发送POST请求的时候，需要给前端回传一个支付页面的Url，前端会直接重定向到这个url
    alipay_url = serializers.SerializerMethodField(read_only=True)
    def get_alipay_url(self, obj):
        alipay = AliPay(
            # 自己沙箱应用的APPID
            appid="2016091100484002",
            # 如果用户没有再浏览器生成的支付订单中支付，而是通过支付宝app进行了订单支付，此时需要指定一个跳转地址。
            # app_notify_url：只要用户通过支付宝支付成功，支付宝就会回调这个notify_url
            app_notify_url="http://114.116.83.180:8000/trades/alipay/redirect/",
            app_private_key_path=settings.app_private_key_path,
            # 支付宝的公钥，验证支付宝回传消息使用，不是自己生成的应用公钥
            alipay_public_key_path=settings.alipay_public_key_path,
            debug=True,  # 默认False,
            # 如果用户是在浏览器上的支付宝订单页面进行的支付操作，支付完成之后会自动跳转到网站的指定页面return_url。如果用户没有在浏览器上支付，return_url就失效了。
            return_url="http://114.116.83.180:8000/trades/alipay/redirect/"
            # app_notify_url和return_url，只有在支付成功的前提下，支付宝才会回调。
            # app_notify_url: 相当于是支付宝给后台发送的一个通知，告诉后台用户已经支付完成了，当后台接收到这个通知之后，必须给支付宝返回一个success结果，告诉支付宝后台已经接收到这个支付结果通知了。
            # return_url：就是一个简单的支付宝回调，支付宝只负责回调这个url地址，至于这个url地址做了什么事情，与支付宝就无关了，支付宝也不会关心这个url的返回值。
        )

        url = alipay.direct_pay(
            subject=obj.order_sn,
            out_trade_no=obj.order_sn,
            total_amount=obj.order_mount
        )
        # 这个re_url就是支付宝提供的一个扫码支付页面的Url
        re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
        return re_url

    class Meta:
        model = OrderInfo
        fields = "__all__"


