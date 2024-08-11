from rest_framework import serializers
from django.db import models
from appstore_notification.models import Notify, NotificationDetail, Notification


class NotifySerializer(serializers.ModelSerializer):

    class Meta:
        model = Notify

        fields = "__all__"

class NotifyCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notify
        #fields = "__all__"
        exclude = ("user",)

class NotificationDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationDetail

        fields = "__all__"
        
    def create(self, validated_data):
        notificationDetail = super().create(validated_data)
        
        app = validated_data.get('app')
        notifies = Notify.objects.filter(app=app)

        for notify in notifies:
            Notification.objects.create(
                notify=notify, 
                notificationDetail=notificationDetail
            )

        return notificationDetail

class NotificationSerializer(serializers.ModelSerializer):

    notificationDetail = NotificationDetailSerializer()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['status'] = instance.get_status_display()
        return ret

    class Meta:
        model = Notification

        fields = ("id", "notificationDetail", "status")
