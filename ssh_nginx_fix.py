import paramiko

host = "64.188.66.177"
user = "root"
password = "s081109g"
domain = "api.nicegram.click"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("Connected to VPS!")

    # Certbot на некоторых старых/кастомных Ubuntu ставит устаревшие или пустые настройки SSL шифрования в Nginx (/etc/letsencrypt/options-ssl-nginx.conf).
    # Мы принудительно укажем Nginx использовать современные безопасные TLS 1.2 и TLS 1.3 шифры.
    ssl_nginx_conf = """# This file contains important security parameters. If you modify this file
# manually, Certbot will be unable to automatically provide security updates
# for these settings.

ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;

ssl_ciphers \"ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384\";
"""

    sftp = ssh.open_sftp()
    with sftp.open("/etc/letsencrypt/options-ssl-nginx.conf", "w") as f:
        f.write(ssl_nginx_conf)
    sftp.close()
    print("Applied modern SSL ciphers configuration!")

    # Проверим и перезагрузим Nginx
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    if stdout.channel.recv_exit_status() == 0:
        ssh.exec_command("systemctl restart nginx")
        print("Nginx successfully restarted with TLS 1.2/1.3!")
    else:
        print("Error in Nginx config:", stderr.read().decode())

    ssh.close()
except Exception as e:
    print("Error:", e)
