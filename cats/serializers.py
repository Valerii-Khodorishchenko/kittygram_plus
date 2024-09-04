import datetime as dt

import webcolors
from rest_framework import serializers

from .models import Achievement, AchievementCat, Cat, CHOICES, Owner


class Hex2NameColor(serializers.Field):
    # При чтении данных ничего не меняем - просто возвращяем как есть
    def to_representation(self, value):
        return value

    # При записи код цвета конвертируется в его название
    def to_internal_value(self, data):
        # Доверяй но проверяй
        try:
            # Если имя цввета существует, то конвертируем код в название
            data = webcolors.hex_to_name(data)
        except ValueError:
            # Иначе возвращаем ошибку
            raise serializers.ValidationError('Для этого цвета нет имени')
        # Возвращаем данные в новом формате
        return data


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatSerializer(serializers.ModelSerializer):
    # owner = serializers.StringRelatedField(read_only=True)
    achievements = AchievementSerializer(
        required=False,  # Для добавления в БД без этого поля
        # read_only=True,
        many=True
    )
    age = serializers.SerializerMethodField()
    # Теперь поле примет только значение, упомянутое в списке CHOICES
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'owner', 'achievements',
                  'age')

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def create(self, validated_data):
        # Если в исходном запросе не было поля achievements
        if 'achievements' not in self.initial_data:
            # То создайм запись о котике без его достижений
            cat = Cat.objects.create(**validated_data)
            return cat
        # Иначе делаем следующее:
        # Уберём список достижений из словаря validated_data и сохраним его
        achievements = validated_data.pop('achievements')
        # Создаём нового котика пока без достижений, данных нам достаточно
        cat =Cat.objects.create(**validated_data)
        # Для каждого достижения из списка достижений
        for achievement in achievements:
            # Создадим новую запись или получим существующий экземпляр из БД
            current_achievement, status = Achievement.objects.get_or_create(
                **achievement
            )
            # Поместим ссылку на кождое достижение во вспомогательную таблицу
            # Не забыв указать к какому котику оно относится
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat
            )
        return cat


class OwnerSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'cats')
