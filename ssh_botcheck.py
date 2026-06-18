import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)

cmds = [
    "cat /etc/systemd/system/ipoint-bot.service",
    "sqlite3 /var/lib/ipoint/ipoint.db 'SELECT category, COUNT(*) FROM products GROUP BY category;'",
    "journalctl -u ipoint-bot.service --since '30 min ago' --no-pager | grep -iE 'error|traceback|exception|conflict' | tail -30",
    "systemctl is-active ipoint-bot.service",
]
for c in cmds:
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()
ssh.close()
