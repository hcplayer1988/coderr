"""URL configuration for core project."""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('profile_app.api.urls')),
    #path('api/', include('offer_app.api.urls')),
    #path('api/', include('order_app.api.urls')),
    #path('api/', include('reviews_app.api.urls')),
    #path('api/', include('general_app.api.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)