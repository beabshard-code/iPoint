import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)

TOKEN = "8820332779:AAFRx0VbpIOul4aYSqbMsphaIL6rk8E6h1I"


def run(c):
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()


run(f"curl -s https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
ssh.close()
