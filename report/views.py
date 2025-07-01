from django.shortcuts import render
from django.http import HttpResponse
from .models import DailyReport, DailyReportDetail
import csv
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.

@staff_member_required
def export_csv(request):
    # レスポンスの設定
    response = HttpResponse(content_type='text/csv; charset=cp932')
    response['Content-Disposition'] = f'attachment; filename="daily_report_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # CSVライターの設定
    writer = csv.writer(response)
    
    # ヘッダーの書き込み
    writer.writerow([
        '日付', 'ユーザー', '開始時間', '終了時間', '作業内容', '得意先', '担当者', '作業詳細', 
        '報告事項', 'コメント', '上司確認', '提出状態'
    ])
    
    # 日報データの取得
    reports = DailyReport.objects.all().order_by('-date')
    
    # データの書き込み
    for report in reports:
        details = report.details.all()
        if details:
            for detail in details:
                writer.writerow([
                    report.date,
                    report.user.username if report.user else '',
                    detail.start_time,
                    detail.end_time,
                    detail.work_title or '',
                    detail.client or '',
                    detail.responsible_person or '',
                    detail.work_detail or '',
                    report.remarks or '',
                    report.comment or '',
                    '確認済' if report.boss_confirmation else '未確認',
                    '提出済' if report.is_submitted else '下書き'
                ])
        else:
            # 詳細がない場合は空の行を追加
            writer.writerow([
                report.date,
                report.user.username if report.user else '',
                '', '', '', '', '', '',
                report.remarks or '',
                report.comment or '',
                '確認済' if report.boss_confirmation else '未確認',
                '提出済' if report.is_submitted else '下書き'
            ])
    
    return response

def export_view(request):
    return render(request, 'report/export.html')
