import subprocess
import sys

subprocess_list = []

while True:
    user_input = input("Введите желаемое количество клиентов (q - закрыть): ")

    if user_input == "q":
        while subprocess_list:
            subproc = subprocess_list.pop()
            subproc.kill()
        exit()

    else:
        if sys.platform.startswith('win32'):
            subprocess_list.append(subprocess.Popen("python server.py", creationflags=subprocess.CREATE_NEW_CONSOLE))

            for i in range(int(user_input)):
                subprocess_list.append(
                    subprocess.Popen(
                        "python client.py", creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                )

        else:
            subprocess_list.append(subprocess.Popen("python server.py", shell=True))

            for i in range(int(user_input)):
                subprocess_list.append(
                    subprocess.Popen(
                        "python client.py", shell=True
                    )
                )

