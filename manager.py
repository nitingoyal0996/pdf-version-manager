#!/usr/bin/env python3

import os
import re
import time
import shutil
import json
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

class FileVersionHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        # Compile patterns for different file variations
        self.prepare_patterns()
        
        self.last_processed = {}  # Track when files were last processed
        self.cooldown = 2  # Cooldown in seconds
    
    def prepare_patterns(self):
        self.file_patterns = {}
        for folder_config in self.config["folders"]:
            folder_path = os.path.expanduser(folder_config["path"])
            self.file_patterns[folder_path] = []
            
            for base_config in folder_config["base_filenames"]:
                base_filename = base_config["name"]
                name, ext = os.path.splitext(base_filename)
                
                # Create patterns for various filename variations
                patterns = [
                    # Chrome download pattern: (1)filename.ext, (2)filename.ext, etc.
                    (re.compile(r'^\((\d+)\)' + re.escape(base_filename) + '$'), base_filename),
                    
                    # Suffix patterns: filename_copy.ext, filename (1).ext, etc.
                    (re.compile(r'^' + re.escape(name) + r'[ _-]copy\d*' + re.escape(ext) + '$'), base_filename),
                    (re.compile(r'^' + re.escape(name) + r' \(\d+\)' + re.escape(ext) + '$'), base_filename),
                    (re.compile(r'^' + re.escape(name) + r'[ _-]\d+' + re.escape(ext) + '$'), base_filename),
                    
                    # Any variation with base name
                    (re.compile(r'^.*' + re.escape(name) + r'.*' + re.escape(ext) + '$'), base_filename)
                ]
                
                self.file_patterns[folder_path].extend(patterns)
    
    def on_created(self, event):
        if not event.is_directory:
            self.process_file_event(event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.process_file_event(event.dest_path)
    
    def process_file_event(self, file_path):
        current_time = time.time()
    
        # Skip if this file was recently processed
        if file_path in self.last_processed:
            if current_time - self.last_processed[file_path] < self.cooldown:
                return
        
        # Update the last processed time
        self.last_processed[file_path] = current_time
        
        dir_path = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        # Skip temporary files
        if filename.startswith('.') or filename.endswith('.crdownload') or filename.endswith('.download'):
            return
        
        # Check if this directory is monitored
        for folder_config in self.config["folders"]:
            folder_path = os.path.expanduser(folder_config["path"])
            
            if os.path.normpath(dir_path) == os.path.normpath(folder_path):
                # Check if this file matches any of our patterns
                self.check_file_match(file_path, filename, folder_path)
    
    def check_file_match(self, file_path, filename, folder_path):
        # Skip our own versioned files
        if re.search(r'_v\d{4}-\d{2}-\d{2}', filename):
            return
            
        patterns = self.file_patterns.get(folder_path, [])
        
        for pattern, base_filename in patterns:
            if pattern.match(filename):
                # This is a variation of a base file we're tracking
                if filename != base_filename:  # Only process if it's not exactly the base filename
                    self.version_files(folder_path, file_path, filename, base_filename)
                break
    
    def version_files(self, folder_path, file_path, filename, base_filename):
        base_path = os.path.join(folder_path, base_filename)
        
        # If the base file already exists, version it
        if os.path.exists(base_path):
            # Generate version string with date
            timestamp = datetime.now().strftime("%Y-%m-%d")
            name, ext = os.path.splitext(base_filename)
            versioned_filename = f"{name}_v{timestamp}{ext}"
            versioned_path = os.path.join(folder_path, versioned_filename)
            
            # If this versioned file already exists, add a counter
            counter = 1
            while os.path.exists(versioned_path):
                versioned_filename = f"{name}_v{timestamp}_{counter}{ext}"
                versioned_path = os.path.join(folder_path, versioned_filename)
                counter += 1
            
            # Move the current base file to the versioned name
            shutil.move(base_path, versioned_path)
            print(f"Versioned: {base_filename} → {versioned_filename}")
        
        # Move the new file to become the base file
        shutil.move(file_path, base_path)
        print(f"Updated: {filename} → {base_filename}")

def load_config(config_path):
    try:
        with open(os.path.expanduser(config_path), 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Config error: {e}")
        print("Creating a new default configuration file...")
        return create_default_config(config_path)

def create_default_config(config_path):
    default_config = {
        "folders": [
            {
                "path": "~/Downloads",
                "base_filenames": [
                    {"name": "statement.pdf"},
                    {"name": "invoice.pdf"},
                    {"name": "report.pdf"}
                ]
            }
        ]
    }
    
    config_dir = os.path.dirname(os.path.expanduser(config_path))
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    with open(os.path.expanduser(config_path), 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print(f"Created default configuration at {config_path}")
    return default_config

def start_monitoring(config):
    event_handler = FileVersionHandler(config)
    observer = Observer()
    
    for folder_config in config["folders"]:
        folder_path = os.path.expanduser(folder_config["path"])
        
        if not os.path.exists(folder_path):
            print(f"Warning: Folder {folder_path} does not exist. Creating it...")
            os.makedirs(folder_path)
        
        print(f"Monitoring folder: {folder_path}")
        print(f"  Base filenames: {[base['name'] for base in folder_config['base_filenames']]}")
        
        observer.schedule(event_handler, folder_path, recursive=False)
    
    observer.start()
    print("File Version Manager is running. Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor folders for file versioning')
    parser.add_argument('--config', default='/Users/ngoyal/Personal/Develop/AutoFileVersion/config.json', 
                        help='Path to configuration file')
    args = parser.parse_args()
    
    config_path = args.config
    config = load_config(config_path)
    start_monitoring(config)