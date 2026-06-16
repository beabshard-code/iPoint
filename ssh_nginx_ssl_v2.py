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

    # Полностью перепишем конфиг Nginx для api.nicegram.click с современными и обратно-совместимыми шифрами
    # напрямую в виртуальный хост, чтобы не зависеть от внешних файлов certbot-a
    nginx_conf = f"""server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {domain};

    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;

    # Надежные и совместимые шифры от Mozilla (Modern/Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-CHACHA20-POLY1305';

    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    sftp = ssh.open_sftp()
    with sftp.open(f"/etc/nginx/sites-available/{domain}", "w") as f:
        f.write(nginx_conf)
    sftp.close()
    print("Applied complete Nginx SSL virtual host config!")

    # Проверяем и перезагружаем Nginx
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    if stdout.channel.recv_exit_status() == 0:
        ssh.exec_command("systemctl restart nginx")
        print("Nginx successfully restarted and running with secure SSL!")
    else:
        print("Nginx config error:", stderr.read().decode())

    ssh.close()
except Exception as e:
    print("Error:", e)
