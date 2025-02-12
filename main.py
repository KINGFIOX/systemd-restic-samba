import subprocess
import re
import os
from sys import stderr


def list_smb_shares(host, username, password):
    # build smbclient command
    command = ["smbclient", "-U", f"{username}%{password}", "-L", host]

    # execute command and get output
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"error: {result.stderr}", file=stderr)
        return []

    shares = []
    # parse output
    for line in result.stdout.split("\n"):
        # use regex to match share name
        match = re.match(r"\s*(\S+)\s+Disk", line)
        if match:
            shares.append(match.group(1))

    shares.remove("NETLOGON")
    shares.remove("SYSVOL")
    return shares


def mount_share_p(host, user, passwd, base):
    # get share list
    shares = list_smb_shares(host, user, passwd)

    # umount previous mounts
    print(f"it is normal that: umount: xxx not mounted.")
    for share in shares:
        mount_point = f"{base}/{share}"
        umount = ["umount", "-f", mount_point]
        subprocess.run(umount)

    # create share directories
    for share in shares:
        mount_point = f"{base}/{share}"
        mkdir = ["mkdir", "-p", mount_point]
        subprocess.run(mkdir)

    # mount shares
    for share in shares:
        mount_point = f"{base}/{share}"
        cifs = [
            "mount.cifs",
            f"//{host}/{share}",
            mount_point,
            "-o",
            f"ro,username={user},password={passwd}",
        ]
        subprocess.run(cifs)


def restic_backup(src, repo, passwd):
    restic = ["restic", "backup", src, "--repo", repo]
    proc = subprocess.run(restic, env={"RESTIC_PASSWORD": passwd})

    # Check for the exit code of the process
    if proc.returncode != 0:
        print(f"Backup failed with exit code {proc.returncode}", file=stderr)
    else:
        print("Backup completed successfully")


def mount_sshfs(host, user, remote_dir, mountpoint):
    subprocess.run(["mkdir", "-p", mountpoint])
    sshfs = ["sshfs", "-o", "ro", f"{user}@{host}:{remote_dir}", mountpoint]
    subprocess.run(sshfs)


def main():
    # check if running as root
    assert os.getuid() == 0, "must run as root"
    assert os.getgid() == 0, "must run as root"

    repo_path = "/home/backup/repo"
    repo_passwd = "22240076"

    # set connection parameters
    samba = "/mnt/data.lan"
    mount_share_p(host="data.lan", user="Administrator", passwd="admin123.", base=samba)
    # restic backup
    restic_backup(samba, repo=repo_path, passwd=repo_passwd)

    # mount sshfs
    sshfs = "/mnt/kisserver.lan"
    mount_sshfs(
        host="kisserver.lan",
        user="Administrator",
        remote_dir="/V:/",
        mountpoint=sshfs,
    )
    # restic backup
    restic_backup(sshfs, repo=repo_path, passwd=repo_passwd)


if __name__ == "__main__":
    import systemd.daemon

    systemd.daemon.notify("READY=1")
    main()
