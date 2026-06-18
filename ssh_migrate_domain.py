import paramiko
import sys

import os
host = os.environ.get("IPOINT_VPS_HOST", "64.188.66.177")
user = os.environ.get("IPOINT_VPS_USER", "root")
password = os.environ.get("IPOINT_VPS_PASSWORD", "")
domain = "ipointshop.xyz"
if not password:
    raise SystemExit("ERROR: set IPOINT_VPS_PASSWORD env var before running.")


def run(ssh, cmd, show=True):
    if show:
        print(f"$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "ignore").strip()
    err = stderr.read().decode("utf-8", "ignore").strip()
    if out:
        sys.stdout.buffer.write((out + "\n").encode("utf-8"))
    if err and code != 0:
        sys.stdout.buffer.write((f"[err {code}] {err}\n").encode("utf-8"))
    sys.stdout.flush()
    return code


try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=25)
    print("--- Connected ---")

    run(ssh, "apt-get install -y nginx certbot python3-certbot-nginx")

    nginx_conf = f"""server {{
    listen 80;
    server_name {domain} www.{domain};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 16M;
    }}
}}
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"/etc/nginx/sites-available/{domain}", "w") as f:
        f.write(nginx_conf)
    sftp.close()
    print("Nginx vhost written.")

    run(ssh, f"ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/{domain}")
    run(ssh, "rm -f /etc/nginx/sites-enabled/default")

    if run(ssh, "nginx -t") == 0:
        run(ssh, "systemctl restart nginx")
        print("Nginx restarted.")
    else:
        print("Nginx config test FAILED, aborting SSL.")
        ssh.close()
        sys.exit(1)

    print("Requesting SSL via Certbot...")
    run(ssh, f"certbot --nginx -d {domain} -d www.{domain} --non-interactive --agree-tos -m admin@{domain} --redirect")

    run(ssh, "systemctl reload nginx")
    print("\n--- Domain migration finished ---")
    ssh.close()
except Exception as e:
    print("Error:", e)
