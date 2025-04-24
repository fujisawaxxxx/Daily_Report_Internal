from django.contrib import admin
from django import forms
from .models import DailyReport, DailyReportDetail
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from django.utils.safestring import mark_safe
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import Group, User

logger = logging.getLogger(__name__)

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
    fields = ('start_time', 'end_time', 'work_title', 'work_detail')
    verbose_name = "作業詳細"
    verbose_name_plural = "作業詳細（追加するには「＋」ボタンをクリック）"
    show_change_link = False
    extra = 1  # 常に1行の空行を表示

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj else 8

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        class InitialFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                if not obj:  # 新規作成時のみ初期値をセット
                    # ユーザーのグループに基づいて初期値を設定
                    if request.user.groups.filter(name='パターンB').exists():
                        initial = [
                            {'start_time': '08:30', 'end_time': '09:00'},
                            {'start_time': '09:30', 'end_time': '10:30'},
                            {'start_time': '10:30', 'end_time': '11:30'},
                            {'start_time': '12:30', 'end_time': '13:30'},
                            {'start_time': '13:30', 'end_time': '14:30'},
                            {'start_time': '14:30', 'end_time': '15:30'},
                            {'start_time': '15:30', 'end_time': '16:30'},
                            {'start_time': '16:30', 'end_time': '17:00'},
                        ]
                    else:  # パターンAまたはその他のユーザー
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

    def get_queryset(self, request):
        # 既存のレコードを取得する際に、__str__メソッドの出力を上書き
        qs = super().get_queryset(request)
        for obj in qs:
            obj.__str__ = lambda self: ''  # 空文字列を返すように上書き
        return qs

class DailyReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = DailyReport
        fields = ('date', 'boss_confirmation', 'remarks', 'comment')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 4}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    form = DailyReportForm
    list_display = ('date', 'get_username', 'get_work_titles', 'custom_boss_confirmation')
    list_filter = ('date', 'user', 'boss_confirmation')
    search_fields = ('user__username', 'details__work_title', 'details__work_detail')
    date_hierarchy = 'date'
    ordering = ('-date',)
    inlines = [DailyReportDetailInline]

    fieldsets = (
        (None, {
            'fields': ('date',),
        }),
        ('コメント', {
            'fields': ('comment',),
        }),
        ('確認・報告事項', {
            'fields': ('boss_confirmation', 'remarks'),
            'classes': ('collapse',),
        }),
    )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        # fieldsにcommentが含まれていることを確認
        if 'comment' not in fields:
            fields = list(fields)
            fields.append('comment')
        return fields

    def get_form(self, request, obj=None, **kwargs):
        # リクエストをフォームに渡す
        form = super().get_form(request, obj, **kwargs)
        form.request = request

        if not obj:  # 新規作成時のみ
            form.base_fields['date'].initial = timezone.now().date()
        
        # リーダーおよび管理者以外はコメントフィールドを無効化
        is_superuser = request.user.is_superuser
        is_leader = request.user.groups.filter(name='リーダー').exists()
        logger.info(f"Get form - User: {request.user.username}, Leader: {is_leader}, Super: {is_superuser}")
        
        # commentフィールドの存在チェック
        if 'comment' in form.base_fields:
            if not is_superuser and not is_leader:
                form.base_fields['comment'].widget.attrs['disabled'] = 'disabled'
                form.base_fields['comment'].widget.attrs['readonly'] = 'readonly'
            else:
                # リーダーまたは管理者の場合は編集可能に
                form.base_fields['comment'].widget.attrs.pop('disabled', None)
                form.base_fields['comment'].widget.attrs.pop('readonly', None)
                logger.info(f"Enabled comment field for {request.user.username}")
        
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # スーパーユーザーまたはリーダーグループに所属するユーザーは全ての日報を閲覧可能
        if request.user.is_superuser or request.user.groups.filter(name='リーダー').exists():
            return qs
        return qs.filter(user=request.user)

    def has_view_permission(self, request, obj=None):
        # スーパーユーザーまたはリーダーグループに所属するユーザーは全ての日報を閲覧可能
        if request.user.is_superuser or request.user.groups.filter(name='リーダー').exists():
            return True
        return obj is None or obj.user == request.user

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name='リーダー').exists():
            return True
        return obj is None or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is None or obj.user == request.user

    def custom_boss_confirmation(self, obj):
        # リーダーグループまたはスーパーユーザーの場合は編集可能なチェックボックスを表示
        if self.request.user.is_superuser or self.request.user.groups.filter(name='リーダー').exists():
            checked = 'checked' if obj.boss_confirmation else ''
            return mark_safe(
                '<input type="hidden" name="_boss_confirmation_{0}" value="0">'
                '<input type="checkbox" name="boss_confirmation_{0}" value="1" {1} '
                'onchange="document.getElementById(\'changelist-form\').submit()">'.format(
                    obj.id, checked
                )
            )
        # それ以外のユーザーの場合は読み取り専用の表示
        else:
            return '✓' if obj.boss_confirmation else '✗'
    custom_boss_confirmation.short_description = '上司確認'

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
        
        # リーダーまたは管理者の場合、すべての変更を保存
        is_superuser = request.user.is_superuser
        is_leader = request.user.groups.filter(name='リーダー').exists()
        
        if not is_superuser and not is_leader and 'comment' in form.changed_data:
            # リーダー以外がコメントを変更しようとした場合は元の値に戻す
            logger.warning(f"Non-leader user {request.user.username} attempted to change comment")
            if obj.pk:
                original = DailyReport.objects.get(pk=obj.pk)
                obj.comment = original.comment
        
        super().save_model(request, obj, form, change)

        # 保存ボタンが押されたらユーザーのメールアドレスに通知メールを送信
        self.send_notification_email(request.user, obj)

    def send_notification_email(self, user, report):
        """日報が保存されたことを通知するメールを送信する"""
        subject = f"日報保存通知: {user.username} - {report.date}"
        
        # 作業内容を取得
        work_details = []
        for detail in report.details.all():
            if detail.work_title and detail.start_time and detail.end_time:
                work_details.append(f"{detail.start_time}〜{detail.end_time}: {detail.work_title} - {detail.work_detail or ''}")
        
        # メール本文を作成
        message = f"{user.username}さんの日報が保存されました。\n"
        message += f"日付: {report.date}\n\n"
        
        message += "【作業内容】\n"
        message += "\n".join(work_details) if work_details else "記録なし\n"
        
        message += f"\n【備考】\n{report.remarks or 'なし'}\n"
        
        if report.comment:
            message += f"\n【コメント】\n{report.comment}\n"
        
        message += f"\n【上司確認】: {'済' if report.boss_confirmation else '未確認'}"
        
        from_email = settings.EMAIL_HOST_USER
        
        # 送信先のメールアドレスを設定
        recipient_emails = []
        
        # ユーザー自身のメールアドレスを使用（最優先）
        if user.email:
            recipient_emails.append(user.email)
            
        # 上司のメールアドレス（リーダーグループのメンバー）を取得
        try:
            leader_group = Group.objects.get(name='リーダー')
            leaders = User.objects.filter(groups=leader_group)
            for leader in leaders:
                if leader.email and leader.email != user.email:  # ユーザー自身が上司の場合は重複送信しない
                    recipient_emails.append(leader.email)
        except Group.DoesNotExist:
            pass
        
        # EMAIL_NOTIFICATIONの設定は使用しない
        
        if recipient_emails:  # メールアドレスが設定されている場合のみ送信
            try:
                send_mail(subject, message, from_email, recipient_emails)
                logger.info(f"メール送信成功: {recipient_emails}")
            except Exception as e:
                logger.error(f"メール送信エラー: {e}")

    # リクエストオブジェクトを保存するためのミドルウェア
    def changelist_view(self, request, extra_context=None):
        self.request = request
        
        # POSTリクエストの場合、チェックボックスの変更を処理
        if request.method == 'POST' and (request.user.is_superuser or request.user.groups.filter(name='リーダー').exists()):
            for key in list(request.POST.keys()):
                if key.startswith('boss_confirmation_'):
                    try:
                        report_id = int(key.split('_')[-1])
                        report = DailyReport.objects.get(id=report_id)
                        # チェックされていればTrue、そうでなければFalse
                        report.boss_confirmation = True
                        report.save()
                    except (ValueError, DailyReport.DoesNotExist):
                        pass
                        
                # チェックボックスが外された場合の処理
                elif key.startswith('_boss_confirmation_'):
                    try:
                        report_id = int(key.split('_')[-1])
                        # 対応するチェックボックスがPOSTデータに存在しない場合はFalseにする
                        checkbox_key = 'boss_confirmation_' + str(report_id)
                        if checkbox_key not in request.POST:
                            report = DailyReport.objects.get(id=report_id)
                            report.boss_confirmation = False
                            report.save()
                    except (ValueError, DailyReport.DoesNotExist):
                        pass
        
        return super().changelist_view(request, extra_context)

    list_per_page = 20
    # list_editable = ['boss_confirmation']  # カスタムフィールドに置き換えたので不要

    def get_readonly_fields(self, request, obj=None):
        # デバッグ情報
        is_superuser = request.user.is_superuser
        is_leader = request.user.groups.filter(name='リーダー').exists()
        logger.info(f"User: {request.user.username}, Superuser: {is_superuser}, Leader: {is_leader}")
        
        readonly = list(self.readonly_fields)
        # リーダーグループに属していない場合、boss_confirmationとcommentを読み取り専用にする
        if not is_superuser and not is_leader:
            readonly.extend(['boss_confirmation', 'comment'])
            logger.info(f"Setting readonly fields for {request.user.username}: {readonly}")
        return readonly
