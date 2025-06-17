from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('samal.urls')),
    path('chaining/', include('smart_selects.urls')),
    path('direct-sales/', include('direct_sales.urls', namespace='direct_sales')),
]

# Раздача статических файлов (только в режиме DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
