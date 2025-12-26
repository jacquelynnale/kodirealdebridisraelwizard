# -*- coding: utf-8 -*-
"""
Israel Wizard - Backup and Restore
ישראל וויזארד - גיבוי ושחזור

Handles backup and restore of Kodi configuration, addons, and userdata.
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import json
import zipfile
import shutil
import time
from datetime import datetime

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_DATA = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

HOME_PATH = xbmcvfs.translatePath('special://home/')
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
USERDATA_PATH = xbmcvfs.translatePath('special://userdata/')
DATABASE_PATH = xbmcvfs.translatePath('special://database/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')

# Default backup location
BACKUP_BASE = os.path.join(ADDON_DATA, 'backups')

# Items to backup
BACKUP_ITEMS = {
    'addons': {
        'path': 'addons',
        'label': 'תוספים',
        'description': 'כל התוספים המותקנים',
        'essential': True,
    },
    'addon_data': {
        'path': 'userdata/addon_data',
        'label': 'נתוני תוספים',
        'description': 'הגדרות והעדפות של תוספים',
        'essential': True,
    },
    'database': {
        'path': 'userdata/Database',
        'label': 'בסיס נתונים',
        'description': 'מסד נתונים של קודי',
        'essential': True,
    },
    'keymaps': {
        'path': 'userdata/keymaps',
        'label': 'מיפוי מקשים',
        'description': 'קיצורי מקלדת ושלט',
        'essential': False,
    },
    'playlists': {
        'path': 'userdata/playlists',
        'label': 'רשימות השמעה',
        'description': 'פלייליסטים שמורים',
        'essential': False,
    },
    'thumbnails': {
        'path': 'userdata/Thumbnails',
        'label': 'תמונות ממוזערות',
        'description': 'מטמון תמונות',
        'essential': False,
    },
    'guisettings': {
        'path': 'userdata/guisettings.xml',
        'label': 'הגדרות ממשק',
        'description': 'הגדרות עיצוב וממשק',
        'essential': True,
        'is_file': True,
    },
    'advancedsettings': {
        'path': 'userdata/advancedsettings.xml',
        'label': 'הגדרות מתקדמות',
        'description': 'הגדרות ביצועים',
        'essential': False,
        'is_file': True,
    },
    'sources': {
        'path': 'userdata/sources.xml',
        'label': 'מקורות',
        'description': 'מקורות מדיה',
        'essential': True,
        'is_file': True,
    },
    'favourites': {
        'path': 'userdata/favourites.xml',
        'label': 'מועדפים',
        'description': 'רשימת מועדפים',
        'essential': True,
        'is_file': True,
    },
}


class BackupRestore:
    """Manages backup and restore operations."""
    
    def __init__(self):
        self.dialog = xbmcgui.Dialog()
        self._ensure_backup_dir()
    
    def log(self, message, level=xbmc.LOGINFO):
        """Log message with prefix."""
        xbmc.log(f'{ADDON_ID} BackupRestore: {message}', level)
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        if not os.path.exists(BACKUP_BASE):
            os.makedirs(BACKUP_BASE)
    
    def _get_backup_path(self, item_key):
        """Get full path for backup item."""
        item = BACKUP_ITEMS.get(item_key)
        if not item:
            return None
        return os.path.join(HOME_PATH, item['path'])
    
    def create_backup(self, items=None, backup_name=None, progress_callback=None):
        """
        Create a backup of specified items.
        
        Args:
            items: List of item keys to backup (None = all essential)
            backup_name: Custom backup name (None = auto-generate)
            progress_callback: Optional callback(percent, message)
            
        Returns:
            str: Path to backup file, or None on failure
        """
        try:
            # Default to essential items
            if items is None:
                items = [k for k, v in BACKUP_ITEMS.items() if v.get('essential', False)]
            
            # Generate backup name
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f'israel_wizard_backup_{timestamp}'
            
            backup_path = os.path.join(BACKUP_BASE, f'{backup_name}.zip')
            
            # Calculate total items
            total_items = len(items)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                metadata = {
                    'created': datetime.now().isoformat(),
                    'kodi_version': xbmc.getInfoLabel('System.BuildVersion'),
                    'wizard_version': ADDON.getAddonInfo('version'),
                    'items': items,
                }
                zf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
                
                for i, item_key in enumerate(items):
                    item = BACKUP_ITEMS.get(item_key)
                    if not item:
                        continue
                    
                    source_path = os.path.join(HOME_PATH, item['path'])
                    
                    if progress_callback:
                        percent = int(((i + 1) / total_items) * 100)
                        progress_callback(percent, f'מגבה {item["label"]}...')
                    
                    if not os.path.exists(source_path):
                        self.log(f'Backup item not found: {source_path}', xbmc.LOGWARNING)
                        continue
                    
                    if item.get('is_file', False):
                        # Single file
                        arcname = os.path.join('backup', item['path'])
                        zf.write(source_path, arcname)
                    else:
                        # Directory
                        for root, dirs, files in os.walk(source_path):
                            # Skip certain directories
                            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'temp']]
                            
                            for file in files:
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, HOME_PATH)
                                arcname = os.path.join('backup', rel_path)
                                
                                try:
                                    zf.write(file_path, arcname)
                                except Exception as e:
                                    self.log(f'Could not backup file: {file_path} - {str(e)}', xbmc.LOGWARNING)
            
            # Verify backup
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                self.log(f'Backup created: {backup_path}')
                return backup_path
            
            return None
            
        except Exception as e:
            self.log(f'Backup error: {str(e)}', xbmc.LOGERROR)
            return None
    
    def restore_backup(self, backup_path, items=None, progress_callback=None):
        """
        Restore from a backup file.
        
        Args:
            backup_path: Path to backup ZIP file
            items: List of item keys to restore (None = all)
            progress_callback: Optional callback(percent, message)
            
        Returns:
            bool: Success status
        """
        try:
            if not os.path.exists(backup_path):
                self.log(f'Backup file not found: {backup_path}', xbmc.LOGERROR)
                return False
            
            if not zipfile.is_zipfile(backup_path):
                self.log(f'Invalid backup file: {backup_path}', xbmc.LOGERROR)
                return False
            
            with zipfile.ZipFile(backup_path, 'r') as zf:
                # Read metadata
                try:
                    metadata = json.loads(zf.read('backup_metadata.json').decode('utf-8'))
                    backup_items = metadata.get('items', [])
                except:
                    backup_items = list(BACKUP_ITEMS.keys())
                
                # Filter items if specified
                if items:
                    restore_items = [i for i in items if i in backup_items]
                else:
                    restore_items = backup_items
                
                # Get all files to restore
                all_files = zf.namelist()
                total_files = len(all_files)
                
                for i, member in enumerate(all_files):
                    if member == 'backup_metadata.json':
                        continue
                    
                    # Check if this file belongs to items we want to restore
                    should_restore = False
                    for item_key in restore_items:
                        item = BACKUP_ITEMS.get(item_key)
                        if item and item['path'] in member:
                            should_restore = True
                            break
                    
                    if not should_restore:
                        continue
                    
                    if progress_callback:
                        percent = int(((i + 1) / total_files) * 100)
                        progress_callback(percent, f'משחזר קבצים... ({i + 1}/{total_files})')
                    
                    # Calculate destination path
                    rel_path = member.replace('backup/', '', 1)
                    dest_path = os.path.join(HOME_PATH, rel_path)
                    
                    # Create directory if needed
                    dest_dir = os.path.dirname(dest_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    # Extract file
                    try:
                        with zf.open(member) as src, open(dest_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                    except Exception as e:
                        self.log(f'Could not restore: {dest_path} - {str(e)}', xbmc.LOGWARNING)
            
            self.log(f'Restore completed from: {backup_path}')
            return True
            
        except Exception as e:
            self.log(f'Restore error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def list_backups(self):
        """List available backups."""
        backups = []
        
        if not os.path.exists(BACKUP_BASE):
            return backups
        
        for filename in os.listdir(BACKUP_BASE):
            if filename.endswith('.zip'):
                filepath = os.path.join(BACKUP_BASE, filename)
                try:
                    stat = os.stat(filepath)
                    
                    # Try to read metadata
                    metadata = {}
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zf:
                            metadata = json.loads(zf.read('backup_metadata.json').decode('utf-8'))
                    except:
                        pass
                    
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created': metadata.get('created', datetime.fromtimestamp(stat.st_mtime).isoformat()),
                        'items': metadata.get('items', []),
                    })
                except Exception as e:
                    self.log(f'Error reading backup: {filename} - {str(e)}', xbmc.LOGWARNING)
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def delete_backup(self, backup_path):
        """Delete a backup file."""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                self.log(f'Backup deleted: {backup_path}')
                return True
        except Exception as e:
            self.log(f'Delete backup error: {str(e)}', xbmc.LOGERROR)
        return False
    
    def create_backup_interactive(self):
        """Interactive backup creation with progress dialog."""
        # Ask user what to backup
        items = list(BACKUP_ITEMS.keys())
        labels = [f'{BACKUP_ITEMS[k]["label"]} - {BACKUP_ITEMS[k]["description"]}' for k in items]
        
        # Pre-select essential items
        preselect = [i for i, k in enumerate(items) if BACKUP_ITEMS[k].get('essential', False)]
        
        selected = self.dialog.multiselect('בחר פריטים לגיבוי', labels, preselect=preselect)
        
        if selected is None:
            return
        
        selected_items = [items[i] for i in selected]
        
        if not selected_items:
            self.dialog.notification(ADDON_NAME, 'לא נבחרו פריטים', xbmcgui.NOTIFICATION_INFO)
            return
        
        # Create backup with progress
        progress = xbmcgui.DialogProgress()
        progress.create(ADDON_NAME, 'יוצר גיבוי...')
        
        try:
            def callback(p, m):
                if progress.iscanceled():
                    raise Exception('בוטל על ידי המשתמש')
                progress.update(p, m)
            
            backup_path = self.create_backup(selected_items, progress_callback=callback)
            progress.close()
            
            if backup_path:
                size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2)
                self.dialog.ok(
                    ADDON_NAME,
                    f'[COLOR green]הגיבוי נוצר בהצלחה![/COLOR]\n\n'
                    f'גודל: {size_mb} MB\n'
                    f'מיקום: {backup_path}'
                )
            else:
                self.dialog.notification(ADDON_NAME, 'יצירת גיבוי נכשלה', xbmcgui.NOTIFICATION_ERROR)
                
        except Exception as e:
            progress.close()
            self.dialog.notification(ADDON_NAME, str(e), xbmcgui.NOTIFICATION_ERROR)
    
    def restore_backup_interactive(self):
        """Interactive backup restoration with selection."""
        backups = self.list_backups()
        
        if not backups:
            self.dialog.notification(ADDON_NAME, 'לא נמצאו גיבויים', xbmcgui.NOTIFICATION_INFO)
            return
        
        # Show backup selection
        labels = [
            f'{b["filename"]} ({b["size_mb"]} MB) - {b["created"][:10]}'
            for b in backups
        ]
        
        selected = self.dialog.select('בחר גיבוי לשחזור', labels)
        
        if selected < 0:
            return
        
        backup = backups[selected]
        
        # Confirm restore
        if not self.dialog.yesno(
            ADDON_NAME,
            f'לשחזר מגיבוי?\n\n'
            f'קובץ: {backup["filename"]}\n'
            f'גודל: {backup["size_mb"]} MB\n\n'
            f'[COLOR red]זה יחליף את ההגדרות הנוכחיות![/COLOR]',
            yeslabel='שחזר',
            nolabel='ביטול'
        ):
            return
        
        # Restore with progress
        progress = xbmcgui.DialogProgress()
        progress.create(ADDON_NAME, 'משחזר גיבוי...')
        
        try:
            def callback(p, m):
                if progress.iscanceled():
                    raise Exception('בוטל על ידי המשתמש')
                progress.update(p, m)
            
            success = self.restore_backup(backup['path'], progress_callback=callback)
            progress.close()
            
            if success:
                if self.dialog.yesno(
                    ADDON_NAME,
                    '[COLOR green]השחזור הושלם![/COLOR]\n\n'
                    'יש לאתחל את קודי להחלת השינויים.',
                    yeslabel='אתחל עכשיו',
                    nolabel='מאוחר יותר'
                ):
                    xbmc.executebuiltin('Quit')
            else:
                self.dialog.notification(ADDON_NAME, 'שחזור נכשל', xbmcgui.NOTIFICATION_ERROR)
                
        except Exception as e:
            progress.close()
            self.dialog.notification(ADDON_NAME, str(e), xbmcgui.NOTIFICATION_ERROR)


# Convenience functions
def create_backup_interactive():
    BackupRestore().create_backup_interactive()

def restore_backup_interactive():
    BackupRestore().restore_backup_interactive()

def list_backups():
    return BackupRestore().list_backups()
