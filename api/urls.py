from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Router e registro Viewset
router = DefaultRouter()
router.register(r'administracao', views.AdministracaoViewSet)
router.register(r'professores', views.ProfessoresViewSet)
router.register(r'responsaveis', views.ResponsaveisViewSet)
router.register(r'alunos', views.AlunosViewSet)
router.register(r'materias', views.MateriasViewSet)
router.register(r'classes', views.ClassesViewSet)
router.register(r'avaliacoes', views.AvaliacoesViewSet)
router.register(r'notas', views.NotasViewSet)

# API URLs automáticas pelo Router.
urlpatterns = [
    path('', include(router.urls)),
    # JWT Authentication URLs
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]