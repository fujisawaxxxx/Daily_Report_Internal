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
            'work_detail': forms.TextInput(attrs={'style': 'width: 200px;'}),
            'remarks': forms.TextInput(attrs={'style': 'width: 200px;'}),
        }

class DailyReportDetailInline(admin.TabularInline):
    model = DailyReportDetail
    form = DailyReportDetailForm
    extra = 1  # デフォルトで表示される空のフォームの数
    fields = ('start_time', 'end_time', 'work_title', 'work_detail', 'remarks')
    verbose_name = ""
    verbose_name_plural = "作業詳細（追加するには「＋」ボタンをクリック）"
    show_change_link = False

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
    
    def get_queryset(self, request):
        """ユーザーが見られる日報を制限するメソッド"""
        qs = super().get_queryset(request)
        # スーパーユーザーは全て閲覧可能
        if request.user.is_superuser:
            return qs
        # 一般ユーザーは自分の日報のみ閲覧可能
        return qs.filter(user=request.user)
    
    def has_view_permission(self, request, obj=None):
        """閲覧権限の確認"""
        # スーパーユーザーは常に閲覧可能
        if request.user.is_superuser:
            return True
        # objがNoneの場合はリスト表示の権限チェック
        if obj is None:
            return True
        # 自分の日報のみ閲覧可能
        return obj.user == request.user
    
    def has_change_permission(self, request, obj=None):
        """編集権限の確認"""
        # スーパーユーザーは常に編集可能
        if request.user.is_superuser:
            return True
        # objがNoneの場合はリスト表示の権限チェック
        if obj is None:
            return True
        # 自分の日報のみ編集可能
        return obj.user == request.user
    
    def has_delete_permission(self, request, obj=None):
        """削除権限の確認"""
        # スーパーユーザーは常に削除可能
        if request.user.is_superuser:
            return True
        # objがNoneの場合はリスト表示の権限チェック
        if obj is None:
            return True
        # 自分の日報のみ削除可能
        return obj.user == request.user
    
    def get_username(self, obj):
        return obj.user.username if obj.user else "未設定"
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
