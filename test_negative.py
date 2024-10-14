import pytest
from ssh_checkers import SSHClientWrapper, checkout_negative, getout
import yaml
from datetime import datetime

with open('config.yaml') as f:
    data = yaml.safe_load(f)

@pytest.fixture(scope="session")
def ssh_client():
    client = SSHClientWrapper(data)
    yield client
    client.close()

@pytest.fixture()
def make_folders(ssh_client):
    cmd = f"mkdir -p {data['folder_in']} {data['folder_out']} {data['folder_ext']} {data['folder_ext2']}"
    return checkout_negative(ssh_client, cmd, "")

@pytest.fixture()
def make_files(ssh_client):
    return []

@pytest.fixture()
def clear_folders(ssh_client):
    cmd = (f"rm -rf {data['folder_in']}/* {data['folder_out']}/* "
           f"{data['folder_ext']}/* {data['folder_ext2']}/*")
    return checkout_negative(ssh_client, cmd, "")

@pytest.fixture()
def make_bad_arx(ssh_client):
    cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} {data['folder_out']}/bad_arx "
            f"{data['folder_in']}/*")
    checkout_negative(ssh_client, cmd1, "Everything is Ok")
    cmd2 = f"truncate -s 1 {data['folder_out']}/bad_arx.{data['arc_type']}"
    checkout_negative(ssh_client, cmd2, "")

@pytest.fixture(autouse=True)
def print_time():
    print(f'Start: {datetime.now().strftime("%H:%M:%S.%f")}')
    yield
    print(f'Finish: {datetime.now().strftime("%H:%M:%S.%f")}')

@pytest.fixture(autouse=True)
def stat_log(ssh_client):
    yield
    time = datetime.now().strftime("%H:%M:%S.%f")
    stat = getout(ssh_client, 'cat /proc/loadavg')
    log_cmd = (f"echo 'time:{time} stat:{stat.strip()}' >> stat.txt")
    checkout_negative(ssh_client, log_cmd, '')

class TestNegative:

    def test_step1(self, ssh_client, make_folders, make_bad_arx):
        cmd = (f"cd {data['folder_out']};"
               f" 7z e bad_arx.{data['arc_type']} -o{data['folder_ext']} -y")
        result = checkout_negative(ssh_client, cmd, "ERRORS")
        assert result, "test1 FAIL"

    def test_step2(self, ssh_client, make_folders, make_bad_arx):
        cmd = f"cd {data['folder_out']}; 7z t bad_arx.{data['arc_type']}"
        result = checkout_negative(ssh_client, cmd, "ERRORS")
        assert result, "test2 FAIL"
