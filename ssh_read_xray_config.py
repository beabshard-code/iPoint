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

    stdin, stdout, stderr = ssh.exec_command("cat /usr/local/x-ui/bin/config.json")
    print("\n--- Xray Config ---")
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()
except Exception as e:
    print("Error:", e)
