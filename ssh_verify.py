import paramiko

host = "64.188.66.177"
user = "root"
password = "s081109g"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    
    # Создаем папку uploads и даем полные права для загрузки картинок
    ssh.exec_command("mkdir -p /var/www/ipoint/static/uploads && chmod -R 777 /var/www/ipoint/static/uploads")
    print("Uploads folder permissions set successfully!")
    
    # Проверим запуск
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active ipoint.service")
    print("Service Status:", stdout.read().decode().strip())
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
