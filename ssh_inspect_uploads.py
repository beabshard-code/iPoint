import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)

cmds = [
    "ls -la /var/lib/ipoint",
    "ls -la /var/lib/ipoint/uploads | head -40",
    "ls -l /var/www/ipoint/static/uploads",
    "du -sh /var/lib/ipoint/uploads",
    "find /var/lib/ipoint/uploads -type f | wc -l",
    "sqlite3 /var/lib/ipoint/ipoint.db 'SELECT id,title,images FROM products LIMIT 20;'",
    "df -h /",
    "systemctl list-timers --all | head -30",
    "ls -la /etc/cron.daily /etc/cron.d 2>&1",
    "cat /etc/systemd/system/ipoint-web.service",
    "journalctl -u ipoint-web.service --since '2 days ago' | grep -iE 'error|trace|exception|delete' | tail -40",
]

for c in cmds:
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()

ssh.close()
