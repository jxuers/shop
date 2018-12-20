from rest_framework import serializers
from .models import *

class GoodsSerilizer(serializers.Serializer):
    """
    Serializer: 序列化的基类，虽然写起来麻烦一些，但是定制性高。
    """
    name = serializers.CharField()
    sold_num = serializers.IntegerField(default=0)
    # goods_front_image = serializers.ImageField()
    shop_price = serializers.CharField()
    add_time = serializers.DateTimeField()

    def create(self, validated_data):
        # 当发送POST请求时，接口的POST请求对应的函数在调用serializer.save()，而save()方法是BaseSerializer类中的方法，save()内部在调用BaseSerializer类中的create()方法，但是create()内部没有实现代码，希望在自己的serializer类中实现这个create()方法。
        goods = Goods.objects.create(**validated_data)
        return goods

class GoodsLevelThreeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = "__all__"

class GoodsLevelTwoCategorySerializer(serializers.ModelSerializer):
    sub_cat = GoodsLevelThreeCategorySerializer(many=True)
    class Meta:
        model = GoodsCategory
        fields = "__all__"

class GoodsCategorySerializer(serializers.ModelSerializer):
    # 如果是一级类目，如何获取该类目下的所有二级目录
    sub_cat = GoodsLevelTwoCategorySerializer(many=True)
    class Meta:
        model = GoodsCategory
        fields = "__all__"

class GoodsImage(serializers.ModelSerializer):
    class Meta:
        model = GoodsImage
        fields = ('image', )

class GoodsModelSerializer(serializers.ModelSerializer):
    # 商品对应类别默认显示的是类别id，现在希望展示这个类别的详细信息。
    # 将每一个商品对应的类别对象再一次通过GoodsCategorySerializer进行序列化。
    category = GoodsCategorySerializer()
    images = GoodsImage(many=True)
    class Meta:
        model = Goods
        # fields = ('name', 'sold_num', 'shop_price', 'add_time')
        fields = "__all__"
