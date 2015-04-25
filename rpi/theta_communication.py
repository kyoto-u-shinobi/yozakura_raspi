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


def take_picture(background=False):
    t, p, q_out, q_err = theta_command(new_image=True, download=False)

    if background:
        return q_out
        
    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def download_thumbnail(retake=False, background=False):
    filename = thumb_filename
    output = None

    t, p, q_out, q_err = theta_command(new_image=retake, download=True, get_thumbnail=True, filename=filename)

    if background:
        return q_out
        
    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def download_image(retake=False, background=False):
    filename = img_filename
    output = None

    t, p, q_out, q_err = theta_command(new_image=retake, download=True, get_thumbnail=False, filename=filename)

    if background:
        return q_out

    while output != "Done!":
        try:
            output = q_out.get_nowait()
        except queue.Empty:
            pass


def read_image(filename):
    with open(filename, "rb") as img:
        image = img.read()
    return image


def send_image(filename):
    # In real application, sock would be self.request
    sock.send(str.encode("theta"))
    result = sock.recv(64)
    if pickle.loads(result) == "ready":
        sock.sendall(read_image(filename))


def main():
    import time
    import pickle
    
    thumbnail_queue = None
    image_queue = None
    
    # Get image request from base station.
    thumbnail_queue = download_thumbnail(retake=True, background=True)
    
    while True:  # Main client loop
        # Handle images
        try:
            if thumbnail_queue:
                thumbnail_done = thumbnail_queue.get_nowait()
            elif image_queue:
                image_done = image_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            if thumbnail_done == "Done!":
                image_queue = download_image(retake=False, background=True)  # Start high resolution download
                thumbnail_done = thumbnail_queue = None
                send_image(thumb_filename)
            if image_done == "Done!":
                image_done = image_queue = None
                send_image(img_filename)
        
        # Do the reset of the stuff.


if __name__ == "__main__":
    download_thumbnail(retake=True)
    # Send thumbnail to base station
    thumbnail = read_image(thumb_filename)
    print("Got the thumbnail! {} bytes.".format(len(thumb)))

    download_image()
    # Send image to base station
    image = read_image(img_filename)
    print("Got the image! {} bytes.".format(len(image)))
