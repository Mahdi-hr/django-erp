from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('users/', include('apps.users.urls')),
    path('materials/', include('apps.materials.urls')),
    path('products/', include('apps.products.urls')),
    path('production/', include('apps.production.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('workers/', include('apps.workers.urls')),
    path('customers/', include('apps.customers.urls')),
    path('invoices/', include('apps.invoices.urls')),
    path('sms/', include('apps.sms.urls')),
    path('reports/', include('apps.reports.urls')),
    path('backup/', include('apps.backup.urls')),
    path('settings/', include('apps.settings_app.urls')),
    path('updater/', include('apps.updater.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
