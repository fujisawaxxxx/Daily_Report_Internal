from django.contrib import admin
from django import forms
from .models import DailyReport, DailyReportDetail

class DailyReportDetailForm(forms.ModelForm):
    class Meta:
        model = DailyReportDetail
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 100px;'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 100px;'}),
            'work_title': forms.TextInput(attrs={'style': 'width: 150px;'}),
            'work_detail': forms.Textarea(attrs={'style': 'width: 200px; height: 60px;'}),
            'remarks': forms.Textarea(attrs={'style': 'width: 200px; height: 60px;'}),
        }

class DailyReportDetailInline(admin.TabularInline):
    model = DailyReportDetail
    form = DailyReportDetailForm
    extra = 1  # デフォルトで表示される空のフォームの数
    fields = ('start_time', 'end_time', 'work_title', 'work_detail', 'remarks')

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ('date', 'boss_confirmation')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

# Register your models here.
@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    form = DailyReportForm
    list_display = ('date', 'get_username', 'get_work_titles', 'boss_confirmation')
    list_filter = ('date', 'user', 'boss_confirmation')
    search_fields = ('user__username', 'details__work_title', 'details__work_detail')
    date_hierarchy = 'date'
    ordering = ('-date',)
    inlines = [DailyReportDetailInline]
    
    fieldsets = (
        (None, {
            'fields': ('date', 'boss_confirmation'),
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'ユーザー'
    
    def get_work_titles(self, obj):
        return ", ".join([detail.work_title for detail in obj.details.all()[:3]])
    get_work_titles.short_description = '作業内容'
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新規作成時のみ
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    # kintoneのようなテーブル型のリスト表示を強化
    list_per_page = 20  # 一ページあたりの表示件数
    list_editable = ['boss_confirmation']  # リスト画面から直接編集可能な項目
