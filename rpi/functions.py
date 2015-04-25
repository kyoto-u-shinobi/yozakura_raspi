import subprocess

def theta_command(take_new=False, download=False, get_thumbnail=False, filename="ricoh.py"):
    commands = []
    if take_new:
        commands.append("shutter")
    if download:
        commands.append("download")
        if get_thumbnail:
            commands.append("thumb")
        else:
            commands.append("image")
    return subprocess.check_output(["python2", filename] + commands).decode().split("\n")[-2]
