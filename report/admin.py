from django.contrib import admin
from django import forms
from .models import DailyReport, DailyReportDetail
from django.forms.models import BaseInlineFormSet
from django.utils import timezone

class DailyReportDetailForm(forms.ModelForm):
    class Meta:
        model = DailyReportDetail
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 100px;'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 100px;'}),
            'work_title': forms.TextInput(attrs={'style': 'width: 150px;'}),
            'work_detail': forms.TextInput(attrs={'style': 'width: 200px;'}),
            'remarks': forms.TextInput(attrs={'style': 'width: 200px;'}),
        }

class DailyReportDetailInline(admin.TabularInline):
    model = DailyReportDetail
    form = DailyReportDetailForm
    fields = ('start_time', 'end_time', 'work_title', 'work_detail', 'remarks')
    verbose_name = ""
    verbose_name_plural = "作業詳細（追加するには「＋」ボタンをクリック）"
    show_change_link = False

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj else 8

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        class InitialFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                if not obj:  # 新規作成時のみ初期値をセット
                    initial = [
                        {'start_time': '09:00', 'end_time': '10:00'},
                        {'start_time': '10:00', 'end_time': '11:00'},
                        {'start_time': '11:00', 'end_time': '12:00'},
                        {'start_time': '13:00', 'end_time': '14:00'},
                        {'start_time': '14:00', 'end_time': '15:00'},
                        {'start_time': '15:00', 'end_time': '16:00'},
                        {'start_time': '16:00', 'end_time': '17:00'},
                        {'start_time': '17:00', 'end_time': '17:30'},
                    ]
                    kwargs['initial'] = initial
                super().__init__(*args, **kwargs)
        return InitialFormSet

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ('date', 'boss_confirmation')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # 新規作成時のみ
            form.base_fields['date'].initial = timezone.now().date()
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(user=request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is None or obj.user == request.user

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is None or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is None or obj.user == request.user

    def get_username(self, obj):
        return obj.user.username if obj.user else "未設定"
    get_username.short_description = 'ユーザー'

    def get_work_titles(self, obj):
        titles = [detail.work_title for detail in obj.details.all()[:3] if detail.work_title]
        return ", ".join(titles) if titles else "-"
    get_work_titles.short_description = '作業内容'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    list_per_page = 20
    list_editable = ['boss_confirmation']
