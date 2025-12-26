# -*- coding: utf-8 -*-
"""
Israel Wizard - Core Wizard Functions
ישראל וויזארד - פונקציות ליבה

Handles downloads, extractions, and progress management.
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import hashlib
import zipfile
import shutil
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
import time

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')
HOME_PATH = xbmcvfs.translatePath('special://home/')
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
USERDATA_PATH = xbmcvfs.translatePath('special://userdata/')


class WizardCore:
    """Core wizard functionality for downloads and installations."""
    
    def __init__(self):
        self.dialog = xbmcgui.Dialog()
        self.progress = None
        self.cancelled = False
    
    def log(self, message, level=xbmc.LOGINFO):
        """Log message with addon prefix."""
        xbmc.log(f'{ADDON_ID}: {message}', level)
    
    def notify(self, message, icon=xbmcgui.NOTIFICATION_INFO, time=3000):
        """Show notification."""
        self.dialog.notification(ADDON_NAME, message, icon, time)
    
    def download_file(self, url, destination, progress_callback=None):
        """
        Download a file from URL with progress tracking.
        
        Args:
            url: Source URL
            destination: Local file path
            progress_callback: Optional callback(percent, message)
            
        Returns:
            bool: Success status
        """
        try:
            self.log(f'Downloading: {url}')
            
            # Create request with headers
            headers = {
                'User-Agent': 'Kodi/21.0 (Windows; Israel Wizard)',
                'Accept': '*/*',
            }
            request = Request(url, headers=headers)
            
            response = urlopen(request, timeout=30)
            total_size = int(response.headers.get('Content-Length', 0))
            
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if not xbmcvfs.exists(dest_dir):
                xbmcvfs.mkdirs(dest_dir)
            
            downloaded = 0
            chunk_size = 8192
            
            with open(destination, 'wb') as f:
                while True:
                    if self.cancelled:
                        self.log('Download cancelled by user')
                        return False
                    
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        progress_callback(percent, f'מוריד: {size_mb:.1f}/{total_mb:.1f} MB')
            
            self.log(f'Download complete: {destination}')
            return True
            
        except HTTPError as e:
            self.log(f'HTTP Error: {e.code} - {url}', xbmc.LOGERROR)
            return False
        except URLError as e:
            self.log(f'URL Error: {e.reason}', xbmc.LOGERROR)
            return False
        except Exception as e:
            self.log(f'Download error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def extract_zip(self, zip_path, destination, progress_callback=None):
        """
        Extract a ZIP file with progress tracking.
        
        Args:
            zip_path: Path to ZIP file
            destination: Extraction destination
            progress_callback: Optional callback(percent, message)
            
        Returns:
            bool: Success status
        """
        try:
            self.log(f'Extracting: {zip_path}')
            
            if not zipfile.is_zipfile(zip_path):
                self.log(f'Invalid ZIP file: {zip_path}', xbmc.LOGERROR)
                return False
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                members = zf.namelist()
                total = len(members)
                
                for i, member in enumerate(members):
                    if self.cancelled:
                        self.log('Extraction cancelled by user')
                        return False
                    
                    zf.extract(member, destination)
                    
                    if progress_callback:
                        percent = int(((i + 1) / total) * 100)
                        progress_callback(percent, f'מחלץ: {i + 1}/{total}')
            
            self.log(f'Extraction complete: {destination}')
            return True
            
        except zipfile.BadZipFile:
            self.log(f'Bad ZIP file: {zip_path}', xbmc.LOGERROR)
            return False
        except Exception as e:
            self.log(f'Extraction error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def calculate_md5(self, file_path):
        """Calculate MD5 hash of a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.log(f'MD5 calculation error: {str(e)}', xbmc.LOGERROR)
            return None
    
    def verify_file(self, file_path, expected_md5):
        """Verify file integrity using MD5."""
        actual_md5 = self.calculate_md5(file_path)
        if actual_md5 and actual_md5 == expected_md5:
            self.log(f'File verified: {file_path}')
            return True
        self.log(f'File verification failed: {file_path}', xbmc.LOGWARNING)
        return False
    
    def clean_temp(self):
        """Clean temporary files."""
        try:
            wizard_temp = os.path.join(TEMP_PATH, 'israelwizard')
            if os.path.exists(wizard_temp):
                shutil.rmtree(wizard_temp)
            self.log('Temp cleaned')
        except Exception as e:
            self.log(f'Clean temp error: {str(e)}', xbmc.LOGERROR)
    
    def get_json(self, url):
        """Fetch and parse JSON from URL."""
        try:
            headers = {
                'User-Agent': 'Kodi/21.0 (Israel Wizard)',
                'Accept': 'application/json',
            }
            request = Request(url, headers=headers)
            response = urlopen(request, timeout=15)
            return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            self.log(f'JSON fetch error: {str(e)}', xbmc.LOGERROR)
            return None
    
    def kodi_version(self):
        """Get current Kodi version."""
        try:
            version = xbmc.getInfoLabel('System.BuildVersion')
            return int(version.split('.')[0])
        except:
            return 21
    
    def execute_json_rpc(self, method, params=None):
        """Execute Kodi JSON-RPC method."""
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'id': 1
        }
        if params:
            request['params'] = params
        
        response = xbmc.executeJSONRPC(json.dumps(request))
        return json.loads(response)
    
    def refresh_addons(self):
        """Refresh addon list."""
        xbmc.executebuiltin('UpdateLocalAddons()')
        xbmc.sleep(500)
    
    def restart_kodi(self):
        """Prompt and restart Kodi."""
        if self.dialog.yesno(ADDON_NAME, 'יש לאתחל את קודי.\n\nלהפעיל מחדש עכשיו?'):
            xbmc.executebuiltin('Quit')
    
    def force_close(self):
        """Force close Kodi without prompt."""
        xbmc.executebuiltin('Quit')


# Convenience functions for direct import
def download_file(url, destination, progress_callback=None):
    """Download file wrapper."""
    return WizardCore().download_file(url, destination, progress_callback)


def extract_zip(zip_path, destination, progress_callback=None):
    """Extract ZIP wrapper."""
    return WizardCore().extract_zip(zip_path, destination, progress_callback)


def calculate_md5(file_path):
    """MD5 calculation wrapper."""
    return WizardCore().calculate_md5(file_path)


def get_kodi_version():
    """Get Kodi version wrapper."""
    return WizardCore().kodi_version()
