# -*- coding: utf-8 -*-
"""
Israel Wizard - Addon Installer
ישראל וויזארד - מתקין תוספים

Handles automatic installation of video addons, subtitles, and utilities.
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import time
import json

try:
    from resources.lib.wizard_core import WizardCore
    from resources.lib.repo_manager import RepoManager
except ImportError:
    from wizard_core import WizardCore
    from repo_manager import RepoManager

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')


# Addon definitions by category
VIDEO_ADDONS = {
    'pov': {
        'id': 'plugin.video.pov',
        'name': 'POV',
        'repo': 'repository.kodifitzwell',
        'description': 'סטרימינג באיכות גבוהה עם Real Debrid',
        'priority': 1,
        'essential': True,
    },
    'otaku': {
        'id': 'plugin.video.otaku',
        'name': 'Otaku',
        'repo': 'repository.hooty',
        'description': 'צפייה באנימה',
        'priority': 2,
        'essential': False,
    },
    'youtube': {
        'id': 'plugin.video.youtube',
        'name': 'YouTube',
        'repo': 'repository.xbmc.org',
        'description': 'YouTube הרשמי',
        'priority': 3,
        'essential': True,
    },
    'idanplus': {
        'id': 'plugin.video.idanplus',
        'name': 'עידן פלוס',
        'repo': 'repository.fishenzon',
        'description': 'טלוויזיה ישראלית - ערוצים ותכניות',
        'priority': 4,
        'essential': True,
    },
}

SUBTITLE_ADDONS = {
    'allsubsplus': {
        'id': 'service.subtitles.all_subs_plus',
        'name': 'All Subs Plus',
        'repo': 'repository.burekas',
        'description': 'כתוביות מכל המקורות',
        'priority': 1,
        'essential': True,
    },
    'darksubs': {
        'id': 'service.subtitles.darksubs',
        'name': 'DarkSubs',
        'repo': 'repository.burekas',
        'description': 'כתוביות עבריות איכותיות',
        'priority': 2,
        'essential': True,
    },
    'localsubtitle': {
        'id': 'service.subtitles.localsubtitle',
        'name': 'LocalSubtitle',
        'repo': 'repository.xbmc.org',
        'description': 'כתוביות מקומיות',
        'priority': 3,
        'essential': False,
    },
}

UTILITY_ADDONS = {
    'inputstreamhelper': {
        'id': 'script.module.inputstreamhelper',
        'name': 'InputStream Helper',
        'repo': 'repository.xbmc.org',
        'description': 'עזר לסטרימינג - DRM',
        'priority': 1,
        'essential': True,
    },
    'autocompletion': {
        'id': 'script.keyboardautocompletion',
        'name': 'AutoCompletion Keyboard',
        'repo': 'repository.xbmc.org',
        'description': 'מקלדת עם השלמה אוטומטית',
        'priority': 2,
        'essential': False,
    },
    'speedtest': {
        'id': 'script.speedtest',
        'name': 'Speed Tester',
        'repo': 'repository.xbmc.org',
        'description': 'בדיקת מהירות אינטרנט',
        'priority': 3,
        'essential': False,
    },
}

# Hebrew language pack
LANGUAGE_ADDON = {
    'id': 'resource.language.he_il',
    'name': 'Hebrew Language Pack',
    'repo': 'repository.xbmc.org',
    'description': 'חבילת שפה עברית',
}


class AddonInstaller:
    """Manages addon installation and configuration."""
    
    def __init__(self):
        self.wizard = WizardCore()
        self.repo_manager = RepoManager()
        self.dialog = xbmcgui.Dialog()
        self.installed_addons = self._scan_installed()
    
    def log(self, message, level=xbmc.LOGINFO):
        """Log message with prefix."""
        xbmc.log(f'{ADDON_ID} AddonInstaller: {message}', level)
    
    def _scan_installed(self):
        """Scan for installed addons."""
        installed = []
        try:
            request = {
                'jsonrpc': '2.0',
                'method': 'Addons.GetAddons',
                'params': {'enabled': True},
                'id': 1
            }
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            if 'result' in response and 'addons' in response['result']:
                for addon in response['result']['addons']:
                    installed.append(addon['addonid'])
        except Exception as e:
            self.log(f'Scan installed error: {str(e)}', xbmc.LOGERROR)
        return installed
    
    def is_installed(self, addon_id):
        """Check if addon is installed."""
        return addon_id in self.installed_addons or os.path.exists(os.path.join(ADDONS_PATH, addon_id))
    
    def install_addon_from_repo(self, addon_id, wait_time=10):
        """
        Install addon from repository.
        
        Args:
            addon_id: Kodi addon ID
            wait_time: Seconds to wait for installation
            
        Returns:
            bool: Success status
        """
        if self.is_installed(addon_id):
            self.log(f'Addon already installed: {addon_id}')
            return True
        
        try:
            # Install via Kodi
            xbmc.executebuiltin(f'InstallAddon({addon_id})')
            
            # Wait for installation
            for _ in range(wait_time * 2):
                xbmc.sleep(500)
                if self.is_installed(addon_id):
                    self.log(f'Addon installed: {addon_id}')
                    self.installed_addons.append(addon_id)
                    return True
            
            self.log(f'Addon install timeout: {addon_id}', xbmc.LOGWARNING)
            return False
            
        except Exception as e:
            self.log(f'Addon install error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def install_addon(self, addon_key, category='video', progress_callback=None):
        """
        Install a specific addon by key.
        
        Args:
            addon_key: Addon key from definitions
            category: 'video', 'subtitle', or 'utility'
            progress_callback: Optional callback(percent, message)
            
        Returns:
            bool: Success status
        """
        # Get addon info
        addons_dict = {
            'video': VIDEO_ADDONS,
            'subtitle': SUBTITLE_ADDONS,
            'utility': UTILITY_ADDONS,
        }
        
        if category not in addons_dict:
            return False
        
        if addon_key not in addons_dict[category]:
            return False
        
        addon_info = addons_dict[category][addon_key]
        addon_id = addon_info['id']
        repo = addon_info['repo']
        
        # First ensure repository is installed
        if progress_callback:
            progress_callback(10, f'בודק מאגר {repo}...')
        
        # Check if repo is installed
        repo_path = os.path.join(ADDONS_PATH, repo)
        if not os.path.exists(repo_path) and repo != 'repository.xbmc.org':
            # Try to install repo
            for repo_key, repo_info in self.repo_manager.REPOSITORIES.items() if hasattr(self.repo_manager, 'REPOSITORIES') else []:
                if repo_info.get('id') == repo:
                    self.repo_manager.install_repo(repo_key)
                    break
        
        # Install the addon
        if progress_callback:
            progress_callback(50, f'מתקין {addon_info["name"]}...')
        
        if self.install_addon_from_repo(addon_id):
            if progress_callback:
                progress_callback(100, f'{addon_info["name"]} הותקן!')
            return True
        
        return False
    
    def install_all_addons(self, progress_callback=None):
        """
        Install all addons from all categories.
        
        Returns:
            dict: Results by category {category: (success, failed)}
        """
        results = {}
        
        all_addons = [
            ('video', VIDEO_ADDONS),
            ('subtitle', SUBTITLE_ADDONS),
            ('utility', UTILITY_ADDONS),
        ]
        
        total_addons = sum(len(addons) for _, addons in all_addons)
        current = 0
        
        for category, addons in all_addons:
            success = 0
            failed = []
            
            sorted_addons = sorted(addons.items(), key=lambda x: x[1]['priority'])
            
            for addon_key, addon_info in sorted_addons:
                current += 1
                percent = int((current / total_addons) * 100)
                
                if progress_callback:
                    progress_callback(percent, f'מתקין {addon_info["name"]}...')
                
                if self.install_addon_from_repo(addon_info['id']):
                    success += 1
                else:
                    failed.append(addon_info['name'])
            
            results[category] = (success, failed)
        
        # Refresh
        self.wizard.refresh_addons()
        
        return results
    
    def install_essential_addons(self, progress_callback=None):
        """Install only essential addons."""
        essential = []
        
        for addons_dict in [VIDEO_ADDONS, SUBTITLE_ADDONS, UTILITY_ADDONS]:
            for key, info in addons_dict.items():
                if info.get('essential', False):
                    essential.append(info)
        
        total = len(essential)
        success = 0
        
        for i, addon_info in enumerate(essential):
            if progress_callback:
                progress_callback(int((i / total) * 100), f'מתקין {addon_info["name"]}...')
            
            if self.install_addon_from_repo(addon_info['id']):
                success += 1
        
        self.wizard.refresh_addons()
        return success
    
    def install_all_addons_interactive(self):
        """Interactive addon installation with progress dialog."""
        progress = xbmcgui.DialogProgress()
        progress.create(ADDON_NAME, 'מתקין תוספים...')
        
        try:
            def callback(p, m):
                if progress.iscanceled():
                    raise Exception('בוטל על ידי המשתמש')
                progress.update(p, m)
            
            results = self.install_all_addons(callback)
            progress.close()
            
            # Build result message
            total_success = sum(r[0] for r in results.values())
            all_failed = []
            for category, (_, failed) in results.items():
                all_failed.extend(failed)
            
            if all_failed:
                self.dialog.ok(
                    ADDON_NAME,
                    f'הותקנו {total_success} תוספים.\n\n'
                    f'נכשלו: {", ".join(all_failed[:5])}'
                )
            else:
                self.dialog.notification(
                    ADDON_NAME,
                    f'כל {total_success} התוספים הותקנו בהצלחה!',
                    xbmcgui.NOTIFICATION_INFO
                )
                
        except Exception as e:
            progress.close()
            self.dialog.notification(ADDON_NAME, str(e), xbmcgui.NOTIFICATION_ERROR)
    
    def install_hebrew_language(self):
        """Install Hebrew language pack."""
        return self.install_addon_from_repo(LANGUAGE_ADDON['id'])
    
    def configure_pov_real_debrid(self, rd_token):
        """Configure POV addon with Real Debrid token."""
        try:
            pov_settings = xbmcvfs.translatePath(
                'special://userdata/addon_data/plugin.video.pov/settings.xml'
            )
            
            # Create settings if POV is installed
            if self.is_installed('plugin.video.pov'):
                settings_dir = os.path.dirname(pov_settings)
                if not os.path.exists(settings_dir):
                    os.makedirs(settings_dir)
                
                # Write RD settings
                settings_content = f'''<settings version="2">
    <setting id="rd.enabled" default="true">true</setting>
    <setting id="rd.token">{rd_token}</setting>
    <setting id="rd.priority">90</setting>
</settings>'''
                
                with open(pov_settings, 'w', encoding='utf-8') as f:
                    f.write(settings_content)
                
                self.log('POV Real Debrid configured')
                return True
                
        except Exception as e:
            self.log(f'Configure POV error: {str(e)}', xbmc.LOGERROR)
        
        return False
    
    def get_addon_list(self):
        """Get list of all addons with status."""
        addons = []
        
        for category, addons_dict in [
            ('video', VIDEO_ADDONS),
            ('subtitle', SUBTITLE_ADDONS),
            ('utility', UTILITY_ADDONS),
        ]:
            for key, info in addons_dict.items():
                addons.append({
                    'key': key,
                    'category': category,
                    'id': info['id'],
                    'name': info['name'],
                    'description': info['description'],
                    'installed': self.is_installed(info['id']),
                    'essential': info.get('essential', False),
                })
        
        return addons


# Convenience functions
def install_all_addons(progress_callback=None):
    """Install all addons."""
    return AddonInstaller().install_all_addons(progress_callback)


def install_essential_addons():
    """Install essential addons only."""
    return AddonInstaller().install_essential_addons()


def install_all_addons_interactive():
    """Interactive addon installation."""
    AddonInstaller().install_all_addons_interactive()
