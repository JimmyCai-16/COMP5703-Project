from rest_framework.routers import DefaultRouter
from django.urls import path, include
from file import views

router = DefaultRouter()
router.register('upload', views.UploadFiles, basename='upload')
#router.register('delete', views.DeleteFiles, basename='delete')


urlpatterns = router.urls

app_name = "file"

urlpatterns = [
    path("", include(router.urls)),
    path("delete/", views.DeleteFiles.as_view())
 
]