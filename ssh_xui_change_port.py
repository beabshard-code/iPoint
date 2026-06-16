import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected!")

    # Мы обновим порт 443 на порт 4443 в x-ui.db во всех инбаундах,
    # чтобы освободить 443 порт для Nginx, который должен держать SSL для нашего домена api.nicegram.click.
    commands = [
        "sqlite3 /etc/x-ui/x-ui.db \"UPDATE inbounds SET port = 4443 WHERE port = 443;\"",
        "systemctl restart x-ui",
        "systemctl restart nginx",
        "systemctl status nginx | grep -A 3 -E '(Active:|nginx:)'"
    ]

    for cmd in commands:
        print(f"\nRunning: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='ignore'))
        print(stderr.read().decode('utf-8', errors='ignore'))

    ssh.close()
except Exception as e:
    print("Error:", e)
