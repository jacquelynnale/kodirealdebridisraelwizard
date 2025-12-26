# -*- coding: utf-8 -*-
"""
Israel Wizard - Repository Manager
ישראל וויזארד - מנהל מאגרים

Handles automatic installation and management of Kodi repositories.
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import time
import json
from xml.etree import ElementTree

try:
    from resources.lib.wizard_core import WizardCore
except ImportError:
    from wizard_core import WizardCore

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDONS_PATH = xbmcvfs.translatePath('special://home/addons/')
TEMP_PATH = xbmcvfs.translatePath('special://temp/')


# Repository definitions
REPOSITORIES = {
    'burekas': {
        'id': 'repository.burekas',
        'name': 'Burekas Repository',
        'url': 'https://burekas.github.io/repository.burekas/repository.burekas-1.0.0.zip',
        'icon': 'https://burekas.github.io/repository.burekas/icon.png',
        'description': 'מאגר ברקס - כתוביות וכלים ישראליים',
        'priority': 1,
    },
    'fishenzon': {
        'id': 'repository.fishenzon',
        'name': 'Fishenzon Repository',
        'url': 'https://fishenzon.github.io/repository.fishenzon/repository.fishenzon-1.0.0.zip',
        'icon': 'https://fishenzon.github.io/repository.fishenzon/icon.png',
        'description': 'מאגר פישנזון - עידן פלוס וטלוויזיה ישראלית',
        'priority': 2,
    },
    'kodifitzwell': {
        'id': 'repository.kodifitzwell',
        'name': 'Kodi Fitzwell Repository',
        'url': 'https://kodifitzwell.github.io/repo/repository.kodifitzwell/repository.kodifitzwell-1.0.0.zip',
        'icon': 'https://kodifitzwell.github.io/repo/icon.png',
        'description': 'מאגר POV לסטרימינג',
        'priority': 3,
    },
    'hooty': {
        'id': 'repository.hooty',
        'name': 'Hooty Repository (Otaku)',
        'url': 'https://goldenfreddy0703.github.io/repository.hooty/repository.hooty-1.0.0.zip',
        'icon': 'https://goldenfreddy0703.github.io/repository.hooty/icon.png',
        'description': 'מאגר אוטאקו - אנימה',
        'priority': 4,
    },
    'peno64': {
        'id': 'repository.peno64',
        'name': 'Peno64 Repository',
        'url': 'https://peno64.github.io/repository.peno64/repository.peno64-1.0.0.zip',
        'icon': 'https://peno64.github.io/repository.peno64/icon.png',
        'description': 'מאגר Peno64',
        'priority': 5,
    },
}

# Essential repos for fresh install
ESSENTIAL_REPOS = ['burekas', 'fishenzon', 'kodifitzwell']


class RepoManager:
    """Manages repository installation and updates."""
    
    def __init__(self):
        self.wizard = WizardCore()
        self.dialog = xbmcgui.Dialog()
        self.installed_repos = []
        self._scan_installed()
    
    def log(self, message, level=xbmc.LOGINFO):
        """Log message with prefix."""
        xbmc.log(f'{ADDON_ID} RepoManager: {message}', level)
    
    def _scan_installed(self):
        """Scan for installed repositories."""
        self.installed_repos = []
        for repo_key, repo_info in REPOSITORIES.items():
            repo_path = os.path.join(ADDONS_PATH, repo_info['id'])
            if os.path.exists(repo_path):
                self.installed_repos.append(repo_info['id'])
    
    def is_installed(self, repo_key):
        """Check if repository is installed."""
        if repo_key in REPOSITORIES:
            return REPOSITORIES[repo_key]['id'] in self.installed_repos
        return False
    
    def get_repo_info(self, repo_key):
        """Get repository information."""
        return REPOSITORIES.get(repo_key)
    
    def install_repo(self, repo_key, progress_callback=None):
        """
        Install a single repository.
        
        Args:
            repo_key: Repository key from REPOSITORIES
            progress_callback: Optional callback(percent, message)
            
        Returns:
            bool: Success status
        """
        if repo_key not in REPOSITORIES:
            self.log(f'Unknown repository: {repo_key}', xbmc.LOGERROR)
            return False
        
        repo = REPOSITORIES[repo_key]
        repo_id = repo['id']
        
        # Check if already installed
        if self.is_installed(repo_key):
            self.log(f'Repository already installed: {repo_id}')
            return True
        
        try:
            # Download repository ZIP
            zip_name = f'{repo_id}.zip'
            zip_path = os.path.join(TEMP_PATH, 'israelwizard', zip_name)
            
            if progress_callback:
                progress_callback(10, f'מוריד {repo["name"]}...')
            
            if not self.wizard.download_file(repo['url'], zip_path, progress_callback):
                self.log(f'Failed to download: {repo_id}', xbmc.LOGERROR)
                return False
            
            # Extract to addons folder
            if progress_callback:
                progress_callback(60, f'מתקין {repo["name"]}...')
            
            if not self.wizard.extract_zip(zip_path, ADDONS_PATH, progress_callback):
                self.log(f'Failed to extract: {repo_id}', xbmc.LOGERROR)
                return False
            
            # Enable the repository
            if progress_callback:
                progress_callback(90, f'מפעיל {repo["name"]}...')
            
            self._enable_addon(repo_id)
            
            # Update installed list
            self.installed_repos.append(repo_id)
            
            # Clean up
            try:
                os.remove(zip_path)
            except:
                pass
            
            self.log(f'Repository installed: {repo_id}')
            
            if progress_callback:
                progress_callback(100, f'{repo["name"]} הותקן!')
            
            return True
            
        except Exception as e:
            self.log(f'Install error for {repo_id}: {str(e)}', xbmc.LOGERROR)
            return False
    
    def _enable_addon(self, addon_id):
        """Enable an addon via JSON-RPC."""
        try:
            request = {
                'jsonrpc': '2.0',
                'method': 'Addons.SetAddonEnabled',
                'params': {
                    'addonid': addon_id,
                    'enabled': True
                },
                'id': 1
            }
            response = xbmc.executeJSONRPC(json.dumps(request))
            self.log(f'Enabled addon: {addon_id}')
            xbmc.sleep(200)
            return True
        except Exception as e:
            self.log(f'Enable addon error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def install_all_repos(self, progress_callback=None):
        """
        Install all repositories in priority order.
        
        Args:
            progress_callback: Optional callback(percent, message)
            
        Returns:
            tuple: (success_count, failed_list)
        """
        sorted_repos = sorted(
            REPOSITORIES.items(),
            key=lambda x: x[1]['priority']
        )
        
        total = len(sorted_repos)
        success = 0
        failed = []
        
        for i, (repo_key, repo_info) in enumerate(sorted_repos):
            base_progress = int((i / total) * 100)
            
            def sub_progress(p, m):
                if progress_callback:
                    actual = base_progress + int(p * (100 / total) / 100)
                    progress_callback(actual, m)
            
            if self.install_repo(repo_key, sub_progress):
                success += 1
            else:
                failed.append(repo_info['name'])
        
        # Refresh addon list
        self.wizard.refresh_addons()
        
        return success, failed
    
    def install_essential_repos(self, progress_callback=None):
        """Install only essential repositories."""
        total = len(ESSENTIAL_REPOS)
        success = 0
        
        for i, repo_key in enumerate(ESSENTIAL_REPOS):
            if progress_callback:
                progress_callback(int((i / total) * 100), f'מתקין מאגר {i + 1}/{total}...')
            
            if self.install_repo(repo_key):
                success += 1
        
        self.wizard.refresh_addons()
        return success
    
    def install_all_repos_interactive(self):
        """Interactive repository installation with progress dialog."""
        progress = xbmcgui.DialogProgress()
        progress.create(ADDON_NAME, 'מתקין מאגרים...')
        
        try:
            def callback(p, m):
                if progress.iscanceled():
                    raise Exception('בוטל על ידי המשתמש')
                progress.update(p, m)
            
            success, failed = self.install_all_repos(callback)
            progress.close()
            
            # Show result
            if failed:
                self.dialog.ok(
                    ADDON_NAME,
                    f'הותקנו {success} מאגרים.\n\n'
                    f'נכשלו: {", ".join(failed)}'
                )
            else:
                self.dialog.notification(
                    ADDON_NAME,
                    f'כל {success} המאגרים הותקנו בהצלחה!',
                    xbmcgui.NOTIFICATION_INFO
                )
                
        except Exception as e:
            progress.close()
            self.dialog.notification(ADDON_NAME, str(e), xbmcgui.NOTIFICATION_ERROR)
    
    def get_repo_list(self):
        """Get list of all repositories with status."""
        repos = []
        for key, info in REPOSITORIES.items():
            repos.append({
                'key': key,
                'id': info['id'],
                'name': info['name'],
                'description': info['description'],
                'installed': self.is_installed(key),
                'icon': info.get('icon', ''),
            })
        return repos
    
    def uninstall_repo(self, repo_key):
        """Uninstall a repository."""
        if repo_key not in REPOSITORIES:
            return False
        
        repo_id = REPOSITORIES[repo_key]['id']
        repo_path = os.path.join(ADDONS_PATH, repo_id)
        
        try:
            if os.path.exists(repo_path):
                import shutil
                shutil.rmtree(repo_path)
                self.installed_repos.remove(repo_id)
                self.wizard.refresh_addons()
                self.log(f'Repository uninstalled: {repo_id}')
                return True
        except Exception as e:
            self.log(f'Uninstall error: {str(e)}', xbmc.LOGERROR)
        
        return False


# Convenience functions
def install_all_repos(progress_callback=None):
    """Install all repositories."""
    return RepoManager().install_all_repos(progress_callback)


def install_essential_repos():
    """Install essential repositories."""
    return RepoManager().install_essential_repos()


def install_all_repos_interactive():
    """Interactive installation."""
    RepoManager().install_all_repos_interactive()
