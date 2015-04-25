import queue
import subprocess
import threading


thumb_filename = "theta_thumb.jpg"
img_filename = "theta_img.jpg"


def enqueue_output(proc, q_out, q_err):
    output = None
    while output != "Done!":
        output = proc.stdout.readline().decode().strip()
        error = proc.stderr.readline().decode().strip()

        q_out.put(output)
        q_err.put(error)

    proc.stdout.close()
    proc.stderr.close()


def theta_command(new_image=False, download=False, get_thumbnail=False, filename=None):
    commands = []

    if new_image:
        commands.append("shutter")

    if download:
        commands.append("download")
        if get_thumbnail:
            commands.append("thumb")
        else:
            commands.append("image")
        commands.append(filename if filename is not None else "auto")

    p = subprocess.Popen(["python2", "theta.py"] + commands,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         bufsize=1, close_fds=True)

    q_out = queue.Queue()
    q_err = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(p, q_out, q_err))
    t.daemon = True
    t.start()

    return t, p, q_out, q_err


def take_picture():
    t, p, q_out, q_err = theta_command(new_image=True, download=False)

    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def download_thumbnail(retake=False):
    filename = thumb_filename
    output = None

    t, p, q_out, q_err = theta_command(new_image=retake, download=True, get_thumbnail=True, filename=filename)

    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def download_image(retake=False):
    filename = img_filename
    output = None

    t, p, q_out, q_err = theta_command(new_image=retake, download=True, get_thumbnail=False, filename=filename)

    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def read_image(filename):
    with open(filename, "rb") as img:
        image = img.read()
    return image


def main():
    import time
    import pickle
    
    t, p, q_out, q_err = theta_command(new_image=True, download=True, get_thumbnail=True)
    i = 0
    filename=None
    took_picture = False
    picture_type = None

    while True:
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass
        else:
            if output == "Took picture":
                took_picture = True
            split_output = output.split()
            if split_output[-1].endswith(".JPG"):
                picture_type = split_output[-3]
                filename = split_output[-1]
            if output == "Done!":
                break

    print("Processed returned {}".format(p.returncode))
    if took_picture:
        print("Took a new picture.")
    if output:
        print("The {} was saved as {}".format(picture_type, filename))

    with open(filename, "rb") as image:
        with open("{}.pk".format(filename.split(".")[0]), "wb") as fout:
            pickle.dump(image.read(), fout, protocol=2)


if __name__ == "__main__":
    download_thumbnail(retake=True)
    # Send thumbnail to base station
    thumbnail = read_image(thumb_filename)
    print("Got the thumbnail! {} bytes.".format(len(thumb)))

    download_image()
    # Send image to base station
    image = read_image(img_filename)
    print("Got the image! {} bytes.".format(len(image)))
