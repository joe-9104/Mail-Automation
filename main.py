import subprocess
import time


def main():
  time.sleep(1.25)
  subprocess.Popen(["python", "send_email.py", "start_scheduler"], creationflags=subprocess.CREATE_NEW_CONSOLE)

if __name__ == "__main__":
    main()