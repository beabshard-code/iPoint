import paramiko

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected to VPS!")

    # Проверим, какие процессы слушают 80 и 443 порт
    print("\n--- Ports listening ---")
    stdin, stdout, stderr = ssh.exec_command("ss -tulpn | grep -E ':80|:443'")
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Проверим, что отдается по curl локально на VPS по http и https
    print("\n--- Curl local http ---")
    stdin, stdout, stderr = ssh.exec_command("curl -Iv http://localhost:5000")
    print(stdout.read().decode())
    print(stderr.read().decode())

    print("\n--- Curl public http ---")
    stdin, stdout, stderr = ssh.exec_command("curl -Iv http://64.188.66.177")
    print(stdout.read().decode())
    print(stderr.read().decode())

    print("\n--- Nginx Error Logs (last 20 lines) ---")
    stdin, stdout, stderr = ssh.exec_command("tail -n 20 /var/log/nginx/error.log")
    print(stdout.read().decode())

    ssh.close()
except Exception as e:
    print("Error:", e)
