"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from mcl.views import handle_404, handle_500
from decorator_include import decorator_include
from django.conf.urls import url
from django.views.static import serve



urlpatterns = [
    path('', include('mcl.urls', namespace="mcl")),
    path('admin/', admin.site.urls),
    path('explorer/', include('explorer.urls')), #sql explorer
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='mcl/password_reset_complete.html'),
         name='password_reset_complete'),
    path("select2/", decorator_include(login_required, 'django_select2.urls')),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]

handler404 = handle_404
handler500 = handle_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

