import paramiko
import yaml

class SSHClientWrapper:
    def __init__(self, config):
        self.config = config['ssh']
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if 'password' in self.config and self.config['password']:
            self.client.connect(
                hostname=self.config['host'],
                port=self.config.get('port', 22),
                username=self.config['username'],
                password=self.config['password']
            )
        else:
            self.client.connect(
                hostname=self.config['host'],
                port=self.config.get('port', 22),
                username=self.config['username'],
                key_filename=self.config.get('key_filename')
            )

    def execute(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        return out, err, stdout.channel.recv_exit_status()

    def close(self):
        self.client.close()

def checkout(ssh_client: SSHClientWrapper, cmd, text):
    stdout, stderr, returncode = ssh_client.execute(cmd)
    if text in stdout and returncode == 0:
        return True
    return False

def checkout_negative(ssh_client: SSHClientWrapper, cmd, text):
    stdout, stderr, returncode = ssh_client.execute(cmd)
    if (text in stdout or text in stderr) and returncode != 0:
        return True
    return False

def getout(ssh_client: SSHClientWrapper, cmd):
    stdout, _, _ = ssh_client.execute(cmd)
    return stdout
