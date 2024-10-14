import pytest
from ssh_checkers import SSHClientWrapper, checkout, getout
import random, string, yaml
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
    return checkout(ssh_client, cmd, "")

@pytest.fixture()
def make_files(ssh_client):
    list_of_files = []
    for i in range(data['count']):
        filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        cmd = (f"cd {data['folder_in']}; "
               f"dd if=/dev/urandom of={filename} bs={data['bs']} count=1 iflag=fullblock")
        if checkout(ssh_client, cmd, ''):
            list_of_files.append(filename)
    return list_of_files

@pytest.fixture()
def clear_folders(ssh_client):
    cmd = (f"rm -rf {data['folder_in']}/* {data['folder_out']}/* "
           f"{data['folder_ext']}/* {data['folder_ext2']}/*")
    return checkout(ssh_client, cmd, "")

@pytest.fixture()
def make_sub_folder(ssh_client):
    testfilename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    subfoldername = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    cmd1 = f"cd {data['folder_in']}; mkdir {subfoldername}"
    if not checkout(ssh_client, cmd1, ''):
        return None, None
    cmd2 = (f"cd {data['folder_in']}/{subfoldername}; "
            f"dd if=/dev/urandom of={testfilename} bs={data['bs']} count=1 iflag=fullblock")
    if not checkout(ssh_client, cmd2, ''):
        return subfoldername, None
    return subfoldername, testfilename

@pytest.fixture()
def make_bad_arx(ssh_client):
    cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} {data['folder_out']}/bad_arx "
            f"{data['folder_in']}/*")
    checkout(ssh_client, cmd1, "Everything is Ok")
    cmd2 = f"truncate -s 1 {data['folder_out']}/bad_arx.{data['arc_type']}"
    checkout(ssh_client, cmd2, "")

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
    log_cmd = (f"echo 'time:{time} count:{data['count']} size:{data['bs']} "
               f"stat:{stat.strip()}' >> stat.txt")
    checkout(ssh_client, log_cmd, '')

class TestPositive:

    def test_step1(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result1 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = f"cd {data['folder_out']}; ls"
        result2 = checkout(ssh_client, cmd2, f"arx2.{data['arc_type']}")
        assert result1 and result2, "test1 FAIL"

    def test_step2(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result1 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = (f"cd {data['folder_out']}; "
                f"7z e arx2.{data['arc_type']} -o{data['folder_ext']} -y")
        result2 = checkout(ssh_client, cmd2, "Everything is Ok")
        cmd3 = f"cd {data['folder_ext']}; ls"
        result3 = checkout(ssh_client, cmd3, make_files[0])
        assert result1 and result2 and result3, "test2 FAIL"

    def test_step3(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result2 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = (f"cd {data['folder_out']}; "
                f"7z x arx2.{data['arc_type']} -o{data['folder_ext2']}")
        result1 = checkout(ssh_client, cmd2, "Everything is Ok")
        assert result1 and result2, "test3 FAIL"

    def test_step4(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result1 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = (f"cd {data['folder_out']}; "
                f"7z l arx2.{data['arc_type']}")
        result2 = checkout(ssh_client, cmd2, make_files[0])
        assert result1 and result2, "test4 FAIL"

    def test_step5(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result2 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = (f"cd {data['folder_out']}; "
                f"7z t arx2.{data['arc_type']}")
        result1 = checkout(ssh_client, cmd2, "Everything is Ok")
        assert result1 and result2, "test5 FAIL"

    def test_step6(self, ssh_client, make_folders, clear_folders, make_files):
        cmd = (f"cd {data['folder_in']}; "
               f"7z u {data['folder_out']}/arx2.{data['arc_type']}")
        assert checkout(ssh_client, cmd, "Everything is Ok"), "test6 FAIL"

    def test_step7(self, ssh_client, make_folders, clear_folders, make_files):
        cmd1 = (f"cd {data['folder_in']}; 7z a -t{data['arc_type']} "
                f"{data['folder_out']}/arx2 {data['folder_in']}/*")
        result2 = checkout(ssh_client, cmd1, "Everything is Ok")
        cmd2 = (f"cd {data['folder_out']}; "
                f"7z d arx2.{data['arc_type']}")
        result1 = checkout(ssh_client, cmd2, "Everything is Ok")
        assert result1 and result2, "test7 FAIL"
