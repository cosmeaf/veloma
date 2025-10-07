from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ping_redis, trigger_task, UserRegisterViewSet, UserLoginViewSet

router = DefaultRouter()
router.register(r'register', UserRegisterViewSet, basename='register')
router.register(r'login',    UserLoginViewSet,    basename='login')

urlpatterns = [
    path('', include(router.urls)),
    path('ping/', ping_redis, name='ping_redis'),
    path('trigger/', trigger_task, name='trigger_task'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
