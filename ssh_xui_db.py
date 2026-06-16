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

    # Найдем все db файлы
    stdin, stdout, stderr = ssh.exec_command("find /etc /usr /var -name '*x-ui*.db' 2>/dev/null")
    print("\n--- Database files ---")
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()
except Exception as e:
    print("Error:", e)
