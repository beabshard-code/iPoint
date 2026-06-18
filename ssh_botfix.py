import paramiko
import sys
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("64.188.66.177", username="root", password="s081109g", timeout=25)


def run(c):
    sys.stdout.buffer.write(("\n$ " + c + "\n").encode("utf-8"))
    out = ssh.exec_command(c)[1].read().decode("utf-8", "ignore")
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()


run("systemctl stop ipoint-bot.service")
run("pkill -9 -f run_bot.py; sleep 1; echo killed")
run("ps aux | grep -E 'run_bot|getUpdates' | grep -v grep")
time.sleep(2)
run("systemctl start ipoint-bot.service")
time.sleep(6)
run("journalctl -u ipoint-bot.service --since '40 sec ago' --no-pager | tail -15")
run("systemctl is-active ipoint-bot.service")
ssh.close()
