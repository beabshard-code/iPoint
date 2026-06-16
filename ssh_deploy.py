import paramiko
import time
import sys

host = "64.188.66.177"
user = "root"
password = "s081109g"

WEBAPP_URL = "https://api.nicegram.click"
BOT_TOKEN = "8820332779:AAFRx0VbpIOul4aYSqbMsphaIL6rk8E6h1I"
ADMIN_CHAT_ID = "8229778449"
BOT_USERNAME = "iPoin_Shop_bot"


def execute_command(ssh, cmd):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "ignore").strip()
    err = stderr.read().decode("utf-8", "ignore").strip()
    if out:
        sys.stdout.buffer.write((out + "\n").encode("utf-8"))
        sys.stdout.flush()
    if err and exit_status != 0:
        sys.stdout.buffer.write((f"Error (status {exit_status}): {err}\n").encode("utf-8"))
        sys.stdout.flush()
    return exit_status


try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)
    print("\n--- SSH Connected ---\n")

    execute_command(ssh, "apt-get update && apt-get install -y python3 python3-pip python3-venv git")

    execute_command(ssh, "rm -rf /var/www/ipoint")
    execute_command(ssh, "mkdir -p /var/www")
    execute_command(ssh, "git clone https://github.com/beabshard-code/iPoint.git /var/www/ipoint")

    execute_command(ssh, "python3 -m venv /var/www/ipoint/venv")
    execute_command(ssh, "/var/www/ipoint/venv/bin/pip install --upgrade pip")
    execute_command(ssh, "/var/www/ipoint/venv/bin/pip install -r /var/www/ipoint/requirements.txt")

    env_block = (
        f"Environment=PORT=5000\n"
        f"Environment=BOT_TOKEN={BOT_TOKEN}\n"
        f"Environment=ADMIN_CHAT_ID={ADMIN_CHAT_ID}\n"
        f"Environment=WEBAPP_URL={WEBAPP_URL}\n"
        f"Environment=BOT_USERNAME={BOT_USERNAME}\n"
    )

    web_service = f"""[Unit]
Description=iPoint Flask Web (gunicorn)
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/ipoint
{env_block}ExecStart=/var/www/ipoint/venv/bin/gunicorn --workers 1 --threads 8 --timeout 60 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    bot_service = f"""[Unit]
Description=iPoint Telegram Bot
After=network.target ipoint-web.service

[Service]
User=root
WorkingDirectory=/var/www/ipoint
{env_block}ExecStart=/var/www/ipoint/venv/bin/python run_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    sftp = ssh.open_sftp()
    with sftp.open("/etc/systemd/system/ipoint-web.service", "w") as f:
        f.write(web_service)
    with sftp.open("/etc/systemd/system/ipoint-bot.service", "w") as f:
        f.write(bot_service)
    sftp.close()
    print("Service files generated.")

    execute_command(ssh, "systemctl disable --now ipoint.service 2>/dev/null; rm -f /etc/systemd/system/ipoint.service")
    execute_command(ssh, "systemctl daemon-reload")
    execute_command(ssh, "systemctl enable ipoint-web.service ipoint-bot.service")
    execute_command(ssh, "systemctl restart ipoint-web.service")
    execute_command(ssh, "systemctl restart ipoint-bot.service")

    time.sleep(3)
    execute_command(ssh, "systemctl status ipoint-web.service --no-pager -l")
    execute_command(ssh, "systemctl status ipoint-bot.service --no-pager -l")

    ssh.close()
    print("\n--- Deployment Finished successfully! ---")
except Exception as e:
    print(f"Deployment Failed: {e}")
