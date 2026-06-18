import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)


def run(c):
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()


run("ps aux | grep run_bot | grep -v grep")
run("journalctl -u ipoint-bot.service --since '10 min ago' --no-pager | tail -50")
run("grep -n 'CallbackQueryHandler\\|add_handler\\|cb_stock\\|^async def' /var/www/ipoint/bot.py | tail -30")
ssh.close()
