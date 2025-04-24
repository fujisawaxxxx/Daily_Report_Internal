ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.1.196']

# メール設定
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # GmailのSMTPサーバー（別のメールサービスの場合は変更）
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ag-mails@ag-media.co.jp'  # 送信元のメールアドレス
EMAIL_HOST_PASSWORD = '51wG9ZagYF'  # アプリパスワードまたはメールアカウントのパスワード

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
] 