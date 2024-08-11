from rest_framework import serializers
from file.models import File
from django.conf import settings
class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File

        fields = "__all__"
    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if not "http" in (ret['file']):
            ret['file'] = settings.SITE_URL + ret['file']
        return ret

