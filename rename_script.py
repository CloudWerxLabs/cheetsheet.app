import os

old_name = 'cheatsheet_app.py'
new_name = 'keywhiz_app.py'

os.rename(old_name, new_name)
print(f"Renamed {old_name} to {new_name}")
