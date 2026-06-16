import paramiko
import time

host = "64.188.66.177"
user = "root"
password = "s081109g"

import sys

def execute_command(ssh, cmd):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    
    out = stdout.read().decode('utf-8', 'ignore').strip()
    err = stderr.read().decode('utf-8', 'ignore').strip()
    
    # Выводим в поток с безопасной кодировкой UTF-8 для Windows консоли
    if out:
        sys.stdout.buffer.write((out + "\n").encode('utf-8'))
        sys.stdout.flush()
    if err and exit_status != 0:
        sys.stdout.buffer.write((f"Error (status {exit_status}): {err}\n").encode('utf-8'))
        sys.stdout.flush()
    return exit_status

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)
    print("\n--- SSH Connected ---\n")

    # Обновление пакетов и установка python/git
    execute_command(ssh, "apt-get update && apt-get install -y python3 python3-pip python3-venv git")

    # Подготовка директории
    execute_command(ssh, "rm -rf /var/www/ipoint")
    execute_command(ssh, "mkdir -p /var/www")
    
    # Клонируем репозиторий
    execute_command(ssh, "git clone https://github.com/beabshard-code/iPoint.git /var/www/ipoint")

    # Создаем виртуальное окружение и ставим зависимости
    execute_command(ssh, "python3 -m venv /var/www/ipoint/venv")
    execute_command(ssh, "/var/www/ipoint/venv/bin/pip install --upgrade pip")
    execute_command(ssh, "/var/www/ipoint/venv/bin/pip install -r /var/www/ipoint/requirements.txt")

    # Создаем systemd-сервис для автозапуска и бессмертия приложения
    service_content = """[Unit]
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
Environment=WEBAPP_URL=https://ipoint.onrender.com
Environment=BOT_USERNAME=iPoin_Shop_bot

[Install]
WantedBy=multi-user.target
"""
    
    # Записываем файл сервиса на удаленный сервер
    sftp = ssh.open_sftp()
    with sftp.open("/etc/systemd/system/ipoint.service", "w") as f:
        f.write(service_content)
    sftp.close()
    print("Service file /etc/systemd/system/ipoint.service generated successfully!")

    # Перезапускаем systemd, активируем и запускаем наш сервис
    execute_command(ssh, "systemctl daemon-reload")
    execute_command(ssh, "systemctl enable ipoint.service")
    execute_command(ssh, "systemctl restart ipoint.service")
    
    time.sleep(2)
    execute_command(ssh, "systemctl status ipoint.service")

    ssh.close()
    print("\n--- Deployment Finished successfully! ---")
except Exception as e:
    print(f"Deployment Failed: {e}")
