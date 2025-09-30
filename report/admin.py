from django.contrib import admin, messages
from django import forms
from .models import DailyReport, DailyReportDetail, UserProfile
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from django.utils.safestring import mark_safe
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
import os
from django.urls import reverse
from django.urls import path
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

logger = logging.getLogger(__name__)

# 管理画面のメニューにエクスポートページへのリンクを追加
# admin.site.index_template = 'admin/custom_index.html'

class DailyReportDetailForm(forms.ModelForm):
    class Meta:
        model = DailyReportDetail
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 80px;'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'style': 'width: 80px;'}),
            'work_title': forms.TextInput(attrs={'style': 'width: 500px;'}),
            'client': forms.TextInput(attrs={'style': 'width: 200px;'}),
            'responsible_person': forms.TextInput(attrs={'style': 'width: 150px;'}),
            'work_detail': forms.TextInput(attrs={'style': 'width: 700px;'}),
            'remarks': forms.TextInput(attrs={'style': 'width: 200px;'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # プルダウン設定を削除（テキスト入力に変更）

class DailyReportDetailInline(admin.TabularInline):
    model = DailyReportDetail
    form = DailyReportDetailForm
    fields = ('start_time', 'end_time', 'work_title', 'client', 'responsible_person')
    verbose_name = "作業詳細"
    verbose_name_plural = "作業詳細（追加するには「＋」ボタンをクリック）"
    show_change_link = False
    extra = 0
    can_delete = False  # 削除チェックボックスを非表示にする

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return 0
        if request.user.groups.filter(name='パターンD').exists():
            return 0
        return 7

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        class InitialFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                if not obj:  # 新規作成時のみ初期値をセット
                    # ユーザーのグループに基づいて初期値を設定
                    if request.user.groups.filter(name='パターンD').exists():
                        initial = []
                    elif request.user.groups.filter(name='パターンC').exists():
                        initial = [
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                            {'start_time': '--:--', 'end_time': '--:--'},
                        ]
                    elif request.user.groups.filter(name='パターンB').exists():
                        initial = [
                            {'start_time': '08:30', 'end_time': '09:30'},
                            {'start_time': '09:30', 'end_time': '10:30'},
                            {'start_time': '10:30', 'end_time': '11:30'},
                            {'start_time': '12:30', 'end_time': '13:30'},
                            {'start_time': '13:30', 'end_time': '14:30'},
                            {'start_time': '14:30', 'end_time': '15:30'},
                            {'start_time': '15:30', 'end_time': '17:00'},
                        ]
                    else:  # パターンAまたはその他のユーザー
                        initial = [
                            {'start_time': '09:00', 'end_time': '10:00'},
                            {'start_time': '10:00', 'end_time': '11:00'},
                            {'start_time': '11:00', 'end_time': '12:00'},
                            {'start_time': '13:00', 'end_time': '14:00'},
                            {'start_time': '14:00', 'end_time': '15:00'},
                            {'start_time': '15:00', 'end_time': '16:00'},
                            {'start_time': '16:00', 'end_time': '17:30'},
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
        fields = ('date', 'boss_confirmation', 'remarks', 'comment', 'is_submitted')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 4}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):

    change_form_template = "report/change_form.html"

    form = DailyReportForm
    list_display = ('date', 'user', 'boss_confirmation', 'is_submitted', 'comment')
    list_filter = ('boss_confirmation', 'is_submitted', 'date', 'user')
    search_fields = ('user__username', 'remarks')
    date_hierarchy = 'date'
    ordering = ('-date',)
    inlines = [DailyReportDetailInline]
    
    # 「保存してもう1つ追加」と「保存して編集を続ける」ボタンを非表示にする設定
    save_on_top = False  # 上部の保存ボタンを非表示
    save_as = False  # 「別名で保存」ボタンを非表示

    fieldsets = (
        (None, {
            'fields': (('date', 'boss_confirmation'),),
        }),
        ('確認・報告事項', {
            'fields': ('remarks', 'comment'),
            'classes': ('collapse',),
        }),
    )
    
    # 「保存してもう1つ追加」ボタンを非表示にするメソッド
    def response_add(self, request, obj, post_url_continue=None):
        """「保存してもう1つ追加」ボタンの動作をオーバーライド"""
        return HttpResponseRedirect('../')
    
    # 「保存して編集を続ける」ボタンを非表示にするメソッド
    def response_change(self, request, obj):
        """「保存して編集を続ける」ボタンの動作をオーバーライド"""
        return HttpResponseRedirect('../')

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
        # スーパーユーザーは全ての日報を閲覧可能
        if request.user.is_superuser:
            return qs
        
        # リーダーグループに所属するユーザーは自分の所属グループのメンバーの日報のみ閲覧可能
        if request.user.groups.filter(name='リーダー').exists():
            # ユーザーの所属グループを取得
            user_groups = request.user.groups.all().exclude(name='リーダー')
            if user_groups.exists():
                # 所属グループがある場合は、そのグループのメンバーの日報のみ表示
                users_in_same_groups = User.objects.filter(groups__in=user_groups).distinct()
                return qs.filter(user__in=users_in_same_groups)
            else:
                # リーダー以外の所属グループがない場合は、自分の日報のみ
                return qs.filter(user=request.user)
                
        # それ以外のユーザーは自分の日報のみ閲覧可能
        return qs.filter(user=request.user)

    def has_view_permission(self, request, obj=None):
        # スーパーユーザーは全ての日報を閲覧可能
        if request.user.is_superuser:
            return True
            
        # objがNoneの場合はリストビュー - get_querysetが適切にフィルタリングするので許可
        if obj is None:
            return True
            
        # リーダーの場合は所属グループをチェック
        if request.user.groups.filter(name='リーダー').exists():
            # 自分の日報は閲覧可能
            if obj.user == request.user:
                return True
                
            # 自分が所属する非リーダーグループを取得
            user_groups = request.user.groups.all().exclude(name='リーダー')
            if not user_groups.exists():
                return False
                
            # 対象ユーザーが自分の所属グループに含まれるかチェック
            return obj.user.groups.filter(id__in=user_groups).exists()
            
        # それ以外のユーザーは自分の日報のみ閲覧可能
        return obj.user == request.user

    def has_change_permission(self, request, obj=None):
        # has_view_permissionと同じロジックを使用
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # スーパーユーザーまたはリーダーグループのみ削除可能
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='リーダー').exists():
            return True
        return False

    def custom_boss_confirmation(self, obj):
        is_superuser = self.request.user.is_superuser
        is_leader = self.request.user.groups.filter(name='リーダー').exists()
        can_edit = False
        
        # スーパーユーザーは全ての日報を編集可能
        if is_superuser:
            can_edit = True
        # リーダーの場合、自分のグループのメンバーの日報のみ編集可能
        elif is_leader:
            # 自分の日報は編集可能
            if obj.user == self.request.user:
                can_edit = True
            else:
                # 自分のグループに属するユーザーの日報のみ編集可能
                user_groups = self.request.user.groups.all().exclude(name='リーダー')
                if user_groups.exists() and obj.user.groups.filter(id__in=user_groups).exists():
                    can_edit = True
        
        # リーダーまたはスーパーユーザーで編集権限がある場合は編集可能なチェックボックスを表示
        if can_edit:
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
        submitting = '_save_submit' in request.POST
        drafting   = '_save_draft'  in request.POST

        # is_submitted をボタンで決定（提出ボタンが押された場合のみ変更）
        if submitting:
            obj.is_submitted = True
        # 通常の保存の場合は、既存の提出状態を保持（変更しない）

        # コメント改竄ガード（略）

        # 新規ならユーザー紐付け
        if not change:
            obj.user = request.user

        # まず保存
        super().save_model(request, obj, form, change)

        # ボタンに応じてメール & メッセージ
        if submitting:
            recipient_emails = self.send_notification_email(request.user, obj)
            if recipient_emails:
                email_list = ", ".join(recipient_emails)
                messages.success(request, f"日報が提出されました。メールを送信しました: {email_list}")
            else:
                messages.success(request, "日報が提出されました。（メールアドレスが設定されていないためメールは送信されませんでした）")
        else:
            messages.info(request, "下書きを保存しました")

    def send_notification_email(self, user, report):
        """日報が保存されたことを通知するメールを送信する"""
        subject = f"日報保存通知: {user.username} - {report.date}"
        
        # 作業内容を取得 - より直接的な方法で取得
        work_details = []
        
        # 日報に関連する詳細をすべて取得 - より確実な方法で
        detail_records = DailyReportDetail.objects.filter(report=report)
        
        if detail_records.exists():
            for detail in detail_records:
                # 各フィールドを個別に処理
                start_time_str = str(detail.start_time) if detail.start_time else "未記入"
                end_time_str = str(detail.end_time) if detail.end_time else "未記入"
                work_title_str = detail.work_title if detail.work_title else "未記入"
                responsible_person_str = detail.responsible_person if detail.responsible_person else "-"
                
                # 必ず情報を追加
                entry = f"{start_time_str}〜{end_time_str}: {work_title_str} (担当: {responsible_person_str})"
                work_details.append(entry)
                logger.info(f"メール作業詳細に追加: {entry}")
        else:
            # 詳細レコードがない場合
            work_details.append("作業詳細はありません")
            logger.info("作業詳細レコードが見つかりませんでした")
        
        # デバッグ情報としてログに出力
        logger.info(f"作業詳細件数: {len(work_details)}")
        for i, detail in enumerate(work_details):
            logger.info(f"詳細 {i+1}: {detail}")
        
        # 日報へのURLを作成
        report_url = f"/admin/report/dailyreport/{report.id}/change/"
        # 完全なURLを取得するためのドメイン設定
        domain = None
        
        # .envファイルからURL_SETを取得
        url_set = os.environ.get('URL_SET')
        if url_set:
            domain = url_set
        else:
            # 従来の方法でドメインを取得（バックアップ）
            if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
                for host in settings.ALLOWED_HOSTS:
                    if host not in ['*', 'localhost', '127.0.0.1']:
                        domain = host
                        break
                if not domain:
                    domain = 'localhost:8000'  # デフォルト値
        
        # PythonAnywhereでは'https://'を使用
        if 'pythonanywhere' in domain:
            full_url = f"https://{domain}{report_url}"
        else:
            # 社内サーバー（192.168.1.XXX）またはローカル環境
            # ポート番号が含まれていない場合でも、80番ポート（デフォルト）なので追加不要
            full_url = f"http://{domain}{report_url}"
        
        # メール本文を作成
        message = f"{user.username}さんから日報が提出されました。\n"
        message += f"日付: {report.date}\n\n"
        
        # 日報へのURLを追加
        message += f"日報の詳細を確認する: {full_url}\n\n"
        
        # 報告事項を追加
        message += f"\n【報告事項】\n{report.remarks or 'なし'}\n"
        
        # メール送信用のデバッグログ
        logger.info(f"作成されたメール本文:\n{message}")
        
        from_email = settings.EMAIL_HOST_USER
        
        # 送信先のメールアドレスを設定
        recipient_emails = []
        
        # ログインしているユーザー（提出者）のメールアドレスのみを使用
        if user.email:
            recipient_emails.append(user.email)
        
        # ログインしているユーザーの追加メールアドレスを取得
        try:
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.additional_email:
                recipient_emails.append(user_profile.additional_email)
        except UserProfile.DoesNotExist:
            pass
        
        # EMAIL_NOTIFICATIONの設定は使用しない
        
        if recipient_emails:  # メールアドレスが設定されている場合のみ送信
            try:
                send_mail(subject, message, from_email, recipient_emails)
                logger.info(f"メール送信成功: {recipient_emails}")
            except Exception as e:
                logger.error(f"メール送信エラー: {e}")
        
        return recipient_emails  # 送信先メールアドレスリストを返す

    # リクエストオブジェクトを保存するためのミドルウェア
    def changelist_view(self, request, extra_context=None):
        self.request = request
        
        # POSTリクエストの場合、チェックボックスの変更を処理
        if request.method == 'POST':
            can_edit = request.user.is_superuser
            is_leader = request.user.groups.filter(name='リーダー').exists()
            
            if is_leader or can_edit:
                for key in list(request.POST.keys()):
                    if key.startswith('boss_confirmation_'):
                        try:
                            report_id = int(key.split('_')[-1])
                            report = DailyReport.objects.get(id=report_id)
                            
                            # リーダーの場合、自分のグループのメンバーの日報のみ編集可能
                            if is_leader and not can_edit:
                                user_groups = request.user.groups.all().exclude(name='リーダー')
                                if not report.user.groups.filter(id__in=user_groups).exists() and report.user != request.user:
                                    continue  # 自分のグループ外のユーザーの日報は編集不可
                            
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
                                
                                # リーダーの場合、自分のグループのメンバーの日報のみ編集可能
                                if is_leader and not can_edit:
                                    user_groups = request.user.groups.all().exclude(name='リーダー')
                                    if not report.user.groups.filter(id__in=user_groups).exists() and report.user != request.user:
                                        continue  # 自分のグループ外のユーザーの日報は編集不可
                                
                                report.boss_confirmation = False
                                report.save()
                        except (ValueError, DailyReport.DoesNotExist):
                            pass
        
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = reverse('admin:import_csv')
        return super().changelist_view(request, extra_context=extra_context)

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view), name='import_csv'),
        ]
        return custom_urls + urls
    
    def import_csv_view(self, request):
        return HttpResponseRedirect('/import/csv/')

# UserProfileの管理画面設定
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'additional_email')
    search_fields = ('user__username', 'additional_email')
    
    def get_queryset(self, request):
        # スーパーユーザーは全てのプロファイルを閲覧可能
        if request.user.is_superuser:
            return super().get_queryset(request)
        # それ以外のユーザーは自分のプロファイルのみ
        return super().get_queryset(request).filter(user=request.user)

# UserProfileのインライン設定
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'プロフィール'

# UserAdminを拡張
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# 既存のUserAdminを削除して新しいものを登録
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
