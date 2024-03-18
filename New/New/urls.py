"""
URL configuration for New project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path
from gaz import views
from users import views as user_views
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('auth/', user_views.register, name="auth"),
    path('noperm/', user_views.noperm, name="noperm"),
    path('current/<int:pk>/', views.get_results, name='get_result'),
    path('record/<int:pk>/', views.get_record, name='get_record'),
    path('delete/<int:pk>/', views.result_delete, name='delete_object'),
    path('home/', views.upload, name="upload"),
    path('logout/',views.user_logout,name='logout'),
    path('success/', views.check_terminal, name="check_terminal"),
    # path('success/<int:ok', views.check_terminal, name='check_terminal'),
    # path('success/<int:pk>/', views.update_data, name='update_data'),

    path('admin/', admin.site.urls),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)