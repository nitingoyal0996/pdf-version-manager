```bash

python3 -m venv venv && source venv/bin/activate && python3 -m pip install watchdog

# update config.json and add file_names and folder of interest
vim config.json

# test the changes
python3 manager.py

# enable it as a service
launchctl load ./com.user.pdfversionmanager.plist

# verify logs
cat ~/Library/Logs/pdf_version_manager.err
cat ~/Library/Logs/pdf_version_manager.out

# stop service
launchctl unload ./com.user.pdfversionmanager.plist
```
