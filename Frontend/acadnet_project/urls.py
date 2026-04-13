from django.contrib import admin
from django.urls import path
from app_vistas import views

urlpatterns = [
    path('admin_django/', admin.site.urls), 
    path('', views.login_view, name='login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reportes/', views.reporte_tutor, name='reportes'),
    path('mis-notas/', views.mis_notas, name='mis_notas'),
    path('ver-usuarios/', views.ver_usuarios, name='ver_usuarios'),
    path('top-notas/', views.top_notas_tutor, name='top_notas_tutor'),
    path('tutor/horarios/', views.tutor_horarios, name='tutor_horarios'),
    path('tutor/notas/', views.tutor_notas, name='tutor_notas'),
]
