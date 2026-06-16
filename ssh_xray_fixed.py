import paramiko
import sys

# Установим дефолтную кодировку для вывода в консоль
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected to VPS!")

    def run_cmd(cmd):
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # Заменяем не-ascii символы на безопасные при выводе
        out = stdout.read().decode('utf-8', errors='ignore').replace('●', '*').replace('├', '+').replace('└', '+').replace('│', '|')
        return out

    print("\n--- Xray status ---")
    print(run_cmd("systemctl status x-ui || systemctl status xray"))

    print("\n--- Ports with processes ---")
    print(run_cmd("ss -tulpn | grep -E ':80|:443'"))

    print("\n--- Nginx status ---")
    print(run_cmd("systemctl status nginx"))

    ssh.close()
except Exception as e:
    print("Error:", e)
