import paramiko
import time

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    # Выводим 50 последних строк логов сервиса
    stdin, stdout, stderr = ssh.exec_command("journalctl -u ipoint.service -n 50 --no-pager")
    print(stdout.read().decode('utf-8', 'ignore'))
    
    ssh.close()
except Exception as e:
    print(f"SSH Connection Failed: {e}")
