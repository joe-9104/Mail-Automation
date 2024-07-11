import subprocess
import time


def main():
  while True:
        user_choice = input("Choose an option (1 or 2): \n1. Launch send_email_oo.py\n2. Launch send_email.py\n")
        
        if user_choice == '1':
            time.sleep(1.25)
            subprocess.Popen(["python", "send_email_oo.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            break
        elif user_choice == '2':
            time.sleep(1.25)
            subprocess.Popen(["python", "send_email.py", "start_scheduler"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    main()