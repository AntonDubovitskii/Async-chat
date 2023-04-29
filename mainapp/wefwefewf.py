from datetime import datetime

current_datetime = datetime.now()

a = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

print(a)