import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)

cmds = [
    "sqlite3 /var/lib/ipoint/ipoint.db 'SELECT id,title,images_raw FROM products;'",
    "readlink -f /var/www/ipoint/static/uploads",
    "ls -la /var/www/ipoint/static/ | grep uploads",
]
for c in cmds:
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()
ssh.close()
