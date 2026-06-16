import paramiko
import time
import sys

host = "64.188.66.177"
user = "root"
password = "s081109g"
domain = "api.nicegram.click"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)
    print("Connected to VPS!")

    # Установка Nginx и Certbot для автоматического HTTPS
    stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y nginx certbot python3-certbot-nginx")
    stdout.channel.recv_exit_status()
    print("Nginx and Certbot installed successfully!")

    # Создаем конфиг Nginx для проксирования на Flask (порт 5000)
    nginx_conf = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    sftp = ssh.open_sftp()
    with sftp.open(f"/etc/nginx/sites-available/{domain}", "w") as f:
        f.write(nginx_conf)
    sftp.close()

    # Активируем конфиг Nginx
    ssh.exec_command(f"ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
    ssh.exec_command("rm -f /etc/nginx/sites-enabled/default")
    
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    if stdout.channel.recv_exit_status() == 0:
        ssh.exec_command("systemctl restart nginx")
        print("Nginx configured and restarted successfully!")
    else:
        print("Nginx configuration test failed:", stderr.read().decode())

    # Получаем бесплатный SSL сертификат (HTTPS)
    print("Requesting SSL Certificate via Certbot...")
    stdin, stdout, stderr = ssh.exec_command(f"certbot --nginx -d {domain} --non-interactive --agree-tos -m admin@{domain} --redirect")
    exit_code = stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    if exit_code == 0:
        print("SSL Certificate obtained and applied successfully! HTTPS is now active.")
    else:
        print("SSL generation failed:", stderr.read().decode())

    # Обновляем системный сервис Flask-приложения на использование HTTPS
    service_content = f"""[Unit]
Description=iPoint Flask App & Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/ipoint
ExecStart=/var/www/ipoint/venv/bin/python app.py
Restart=always
RestartSec=5
Environment=PORT=5000
Environment=BOT_TOKEN=8820332779:AAFRx0VbpIOul4aYSqbMsphaIL6rk8E6h1I
Environment=ADMIN_CHAT_ID=8229778449
Environment=WEBAPP_URL=https://{domain}
Environment=BOT_USERNAME=iPoin_Shop_bot

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.open("/etc/systemd/system/ipoint.service", "w") as f:
        f.write(service_content)
    sftp.close()

    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl restart ipoint.service")
    print("System Service updated with HTTPS domain configurations!")
    
    ssh.close()
except Exception as e:
    print("Error:", e)
