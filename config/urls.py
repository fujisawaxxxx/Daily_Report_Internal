"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from report.views import export_csv, export_view, import_csv
from django.shortcuts import redirect

# 管理サイトのタイトルとヘッダーを変更
admin.site.site_header = 'あさひ高速印刷株式会社日報'  # ログインページとヘッダーのタイトル
admin.site.site_title = ''  # ブラウザのタブに表示されるタイトル
admin.site.index_title = 'Daily Report'  # 管理画面のホームページのタイトル

def redirect_to_admin(request):
    return redirect('admin:index')

urlpatterns = [
    path('', redirect_to_admin),  # ルートURLを管理画面にリダイレクト
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # 認証URL追加
    path('export/', export_view, name='export_view'),
    path('export/csv/', export_csv, name='export_csv'),
    path('import/csv/', import_csv, name='import_csv'),
]
