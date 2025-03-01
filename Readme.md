```bash
Author: Nitin Goyal
Co-author: Claud 3.7

# create environment
python3 -m venv venv && source venv/bin/activate && python3 -m pip install watchdog

# update config.json and add file_names and folder of interest
vim config.json

# update default config.json path in manager.py
parser.add_argument('--config', default='your-project-path/config.json', 
                        help='Path to configuration file')
# update program arguments to your project directory path
<key>ProgramArguments</key>
<array>
    <string>your-project-path/venv/bin/python3</string>
    <string>your-project-path/manager.py</string>
</array>

# activate virtual environment
source venv/bin/activate

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
