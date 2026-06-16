import paramiko
import time

host = "64.188.66.177"
user = "root"
password = "s081109g"

# Пробуем подключиться с несколькими попытками при разрыве баннера
for i in range(3):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=15, banner_timeout=15)
        
        stdin, stdout, stderr = ssh.exec_command("journalctl -u ipoint.service -n 50 --no-pager")
        print("--- Service Logs ---")
        print(stdout.read().decode('utf-8', 'ignore'))
        ssh.close()
        break
    except Exception as e:
        print(f"Attempt {i+1} failed: {e}")
        time.sleep(2)
