import paramiko

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected to VPS!")

    # Выведем список файлов в sites-enabled
    stdin, stdout, stderr = ssh.exec_command("ls -l /etc/nginx/sites-enabled/")
    print("\n--- sites-enabled ---")
    print(stdout.read().decode())

    # Проверим, существует ли симлинк на наш конфиг
    stdin, stdout, stderr = ssh.exec_command("ls -l /etc/nginx/sites-enabled/api.nicegram.click")
    res = stdout.read().decode().strip()
    if not res:
        print("Symlink for api.nicegram.click does NOT exist in sites-enabled!")
        print("Creating symlink...")
        ssh.exec_command("ln -s /etc/nginx/sites-available/api.nicegram.click /etc/nginx/sites-enabled/")
        print("Symlink created!")

    # Удалим дефолтный дефолт, который может перехватывать запросы
    print("\n--- checking default site ---")
    ssh.exec_command("rm -f /etc/nginx/sites-enabled/default")
    
    # Проверим сертификаты certbot
    stdin, stdout, stderr = ssh.exec_command("ls -lh /etc/letsencrypt/live/api.nicegram.click/")
    print("\n--- Certbot certificates list ---")
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Тестируем и перезапускаем
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    print("\n--- Nginx test ---")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.exec_command("systemctl restart nginx")
    print("Nginx restarted.")

    ssh.close()
except Exception as e:
    print("Error:", e)
