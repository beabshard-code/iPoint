import paramiko

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected to VPS!")

    # Ищем файлы конфигурации xray
    stdin, stdout, stderr = ssh.exec_command("find /etc /usr -name '*xray*.json' -o -name 'config.json' 2>/dev/null")
    print("\n--- Xray configs found ---")
    print(stdout.read().decode())

    # Посмотрим статус nginx службы
    stdin, stdout, stderr = ssh.exec_command("systemctl status nginx")
    print("\n--- Nginx status ---")
    print(stdout.read().decode())

    # Посмотрим статус xray
    stdin, stdout, stderr = ssh.exec_command("systemctl status xray")
    print("\n--- Xray status ---")
    print(stdout.read().decode())

    ssh.close()
except Exception as e:
    print("Error:", e)
