import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)

cmds = [
    "sqlite3 /var/lib/ipoint/ipoint.db '.tables'",
    "sqlite3 /var/lib/ipoint/ipoint.db 'SELECT COUNT(*) FROM products;'",
    "sqlite3 /var/lib/ipoint/ipoint.db 'SELECT id,title,images,cover FROM products LIMIT 10;' 2>&1",
    "grep -rEl '/var/lib|/tmp|/var/www' /usr/lib/tmpfiles.d/ /etc/tmpfiles.d/ 2>/dev/null",
    "cat /usr/lib/tmpfiles.d/tmp.conf 2>/dev/null",
    "journalctl -u systemd-tmpfiles-clean.service --since '3 days ago' --no-pager | tail -30",
]
for c in cmds:
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()
ssh.close()
