# -*- coding: utf-8 -*-
"""
Israel Wizard - Service Authentication
ישראל וויזארד - אימות שירותים

Handles OAuth and API authentication for Real Debrid, Trakt, MDBList, and Premiumize.
"""

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import os
import json
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_DATA = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

# Ensure addon data directory exists
if not os.path.exists(ADDON_DATA):
    os.makedirs(ADDON_DATA)

# Service configuration
SERVICES_FILE = os.path.join(ADDON_DATA, 'services.json')

# Real Debrid OAuth settings
RD_CLIENT_ID = 'X245A4XAIBGVM'  # Open source client ID
RD_API_BASE = 'https://api.real-debrid.com/rest/1.0'
RD_OAUTH_BASE = 'https://api.real-debrid.com/oauth/v2'
RD_DEVICE_URL = 'https://real-debrid.com/device'
RD_PRIORITY = 90

# Trakt OAuth settings
TRAKT_CLIENT_ID = '0183a05ad97098d87287fe46da4ae286f434f32e8e951caad4cc147c947d79a3'
TRAKT_API_BASE = 'https://api.trakt.tv'
TRAKT_DEVICE_URL = 'https://trakt.tv/activate'

# MDBList settings
MDBLIST_API_BASE = 'https://mdblist.com/api'

# Premiumize settings
PM_CLIENT_ID = 'israelwizard'
PM_API_BASE = 'https://www.premiumize.me/api'


class ServiceAuth:
    """Manages service authentication and token storage."""
    
    def __init__(self):
        self.dialog = xbmcgui.Dialog()
        self.services = self._load_services()
    
    def log(self, message, level=xbmc.LOGINFO):
        """Log message with prefix."""
        xbmc.log(f'{ADDON_ID} ServiceAuth: {message}', level)
    
    def _load_services(self):
        """Load saved service tokens."""
        try:
            if os.path.exists(SERVICES_FILE):
                with open(SERVICES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f'Load services error: {str(e)}', xbmc.LOGERROR)
        return {}
    
    def _save_services(self):
        """Save service tokens."""
        try:
            with open(SERVICES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.services, f, indent=2)
            self.log('Services saved')
        except Exception as e:
            self.log(f'Save services error: {str(e)}', xbmc.LOGERROR)
    
    def _api_request(self, url, data=None, headers=None, method='GET'):
        """Make API request."""
        try:
            if headers is None:
                headers = {}
            
            headers['User-Agent'] = 'Kodi/21.0 Israel Wizard'
            
            if data and method == 'POST':
                data = urlencode(data).encode('utf-8')
            
            request = Request(url, data=data, headers=headers)
            if method != 'GET' and data is None:
                request.get_method = lambda: method
            
            response = urlopen(request, timeout=30)
            return json.loads(response.read().decode('utf-8'))
            
        except HTTPError as e:
            self.log(f'HTTP Error {e.code}: {url}', xbmc.LOGERROR)
        except URLError as e:
            self.log(f'URL Error: {e.reason}', xbmc.LOGERROR)
        except Exception as e:
            self.log(f'API Request error: {str(e)}', xbmc.LOGERROR)
        return None
    
    # =========================================================================
    # REAL DEBRID
    # =========================================================================
    
    def check_real_debrid_status(self):
        """Check if Real Debrid is authenticated."""
        return 'real_debrid' in self.services and 'token' in self.services['real_debrid']
    
    def get_real_debrid_token(self):
        """Get Real Debrid access token."""
        if self.check_real_debrid_status():
            return self.services['real_debrid'].get('token')
        return None
    
    def authenticate_real_debrid(self):
        """
        Authenticate with Real Debrid using device code flow.
        
        Returns:
            bool: Success status
        """
        try:
            # Step 1: Get device code
            device_code_url = f'{RD_OAUTH_BASE}/device/code?client_id={RD_CLIENT_ID}&new_credentials=yes'
            response = self._api_request(device_code_url)
            
            if not response:
                self.dialog.notification(ADDON_NAME, 'שגיאה בקבלת קוד', xbmcgui.NOTIFICATION_ERROR)
                return False
            
            device_code = response.get('device_code')
            user_code = response.get('user_code')
            verification_url = response.get('verification_url', RD_DEVICE_URL)
            expires_in = response.get('expires_in', 600)
            interval = response.get('interval', 5)
            
            # Step 2: Show user the code
            progress = xbmcgui.DialogProgress()
            progress.create(
                'Real Debrid',
                f'[COLOR cyan]פתח:[/COLOR] {verification_url}\n\n'
                f'[COLOR yellow]הזן קוד:[/COLOR] [B]{user_code}[/B]\n\n'
                'ממתין לאישור...'
            )
            
            # Step 3: Poll for authorization
            token_url = f'{RD_OAUTH_BASE}/device/credentials?client_id={RD_CLIENT_ID}&code={device_code}'
            start_time = time.time()
            
            while time.time() - start_time < expires_in:
                if progress.iscanceled():
                    progress.close()
                    return False
                
                elapsed = int(time.time() - start_time)
                percent = int((elapsed / expires_in) * 100)
                progress.update(percent)
                
                xbmc.sleep(interval * 1000)
                
                creds = self._api_request(token_url)
                if creds and 'client_id' in creds:
                    # Got credentials, now get token
                    client_id = creds['client_id']
                    client_secret = creds['client_secret']
                    
                    token_data = {
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'code': device_code,
                        'grant_type': 'http://oauth.net/grant_type/device/1.0'
                    }
                    
                    token_response = self._api_request(
                        f'{RD_OAUTH_BASE}/token',
                        data=token_data,
                        method='POST'
                    )
                    
                    if token_response and 'access_token' in token_response:
                        self.services['real_debrid'] = {
                            'token': token_response['access_token'],
                            'refresh_token': token_response.get('refresh_token'),
                            'client_id': client_id,
                            'client_secret': client_secret,
                            'priority': RD_PRIORITY,
                            'expires': time.time() + token_response.get('expires_in', 604800)
                        }
                        self._save_services()
                        self._configure_rd_in_addons()
                        
                        progress.close()
                        self.dialog.notification(ADDON_NAME, 'Real Debrid מחובר!', xbmcgui.NOTIFICATION_INFO)
                        return True
            
            progress.close()
            self.dialog.notification(ADDON_NAME, 'פג תוקף הקוד', xbmcgui.NOTIFICATION_WARNING)
            return False
            
        except Exception as e:
            self.log(f'RD auth error: {str(e)}', xbmc.LOGERROR)
            return False
    
    def _configure_rd_in_addons(self):
        """Configure Real Debrid in compatible addons."""
        token = self.get_real_debrid_token()
        if not token:
            return
        
        # Configure POV
        pov_data = xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.pov/')
        if os.path.exists(pov_data) or os.path.exists(os.path.join(
            xbmcvfs.translatePath('special://home/addons/'), 'plugin.video.pov'
        )):
            try:
                if not os.path.exists(pov_data):
                    os.makedirs(pov_data)
                
                settings_path = os.path.join(pov_data, 'settings.xml')
                settings_content = f'''<settings version="2">
    <setting id="realdebrid.enabled">true</setting>
    <setting id="realdebrid.token">{token}</setting>
    <setting id="realdebrid.priority">{RD_PRIORITY}</setting>
</settings>'''
                with open(settings_path, 'w', encoding='utf-8') as f:
                    f.write(settings_content)
                self.log('Configured Real Debrid in POV')
            except Exception as e:
                self.log(f'Configure POV error: {str(e)}', xbmc.LOGERROR)
    
    # =========================================================================
    # TRAKT
    # =========================================================================
    
    def check_trakt_status(self):
        """Check if Trakt is authenticated."""
        return 'trakt' in self.services and 'token' in self.services['trakt']
    
    def get_trakt_token(self):
        """Get Trakt access token."""
        if self.check_trakt_status():
            return self.services['trakt'].get('token')
        return None
    
    def authenticate_trakt(self):
        """
        Authenticate with Trakt using device code flow.
        
        Returns:
            bool: Success status
        """
        try:
            # Get device code
            headers = {
                'Content-Type': 'application/json',
                'trakt-api-version': '2',
                'trakt-api-key': TRAKT_CLIENT_ID
            }
            
            device_url = f'{TRAKT_API_BASE}/oauth/device/code'
            device_data = json.dumps({'client_id': TRAKT_CLIENT_ID}).encode('utf-8')
            
            request = Request(device_url, data=device_data, headers=headers)
            response = json.loads(urlopen(request, timeout=30).read().decode('utf-8'))
            
            user_code = response.get('user_code')
            device_code = response.get('device_code')
            verification_url = response.get('verification_url', TRAKT_DEVICE_URL)
            expires_in = response.get('expires_in', 600)
            interval = response.get('interval', 5)
            
            # Show code to user
            progress = xbmcgui.DialogProgress()
            progress.create(
                'Trakt',
                f'[COLOR cyan]פתח:[/COLOR] {verification_url}\n\n'
                f'[COLOR yellow]הזן קוד:[/COLOR] [B]{user_code}[/B]\n\n'
                'ממתין לאישור...'
            )
            
            # Poll for token
            start_time = time.time()
            token_url = f'{TRAKT_API_BASE}/oauth/device/token'
            
            while time.time() - start_time < expires_in:
                if progress.iscanceled():
                    progress.close()
                    return False
                
                elapsed = int(time.time() - start_time)
                progress.update(int((elapsed / expires_in) * 100))
                
                xbmc.sleep(interval * 1000)
                
                try:
                    token_data = json.dumps({
                        'code': device_code,
                        'client_id': TRAKT_CLIENT_ID,
                        'client_secret': ''  # Not needed for device auth
                    }).encode('utf-8')
                    
                    token_request = Request(token_url, data=token_data, headers=headers)
                    token_response = json.loads(urlopen(token_request, timeout=30).read().decode('utf-8'))
                    
                    if 'access_token' in token_response:
                        self.services['trakt'] = {
                            'token': token_response['access_token'],
                            'refresh_token': token_response.get('refresh_token'),
                            'expires': time.time() + token_response.get('expires_in', 7776000)
                        }
                        self._save_services()
                        
                        progress.close()
                        self.dialog.notification(ADDON_NAME, 'Trakt מחובר!', xbmcgui.NOTIFICATION_INFO)
                        return True
                        
                except HTTPError as e:
                    if e.code != 400:  # 400 = pending
                        raise
            
            progress.close()
            self.dialog.notification(ADDON_NAME, 'פג תוקף הקוד', xbmcgui.NOTIFICATION_WARNING)
            return False
            
        except Exception as e:
            self.log(f'Trakt auth error: {str(e)}', xbmc.LOGERROR)
            return False
    
    # =========================================================================
    # MDBLIST
    # =========================================================================
    
    def check_mdblist_status(self):
        """Check if MDBList API key is configured."""
        return 'mdblist' in self.services and 'api_key' in self.services['mdblist']
    
    def get_mdblist_key(self):
        """Get MDBList API key."""
        if self.check_mdblist_status():
            return self.services['mdblist'].get('api_key')
        return None
    
    def save_mdblist_key(self, api_key):
        """Save MDBList API key."""
        self.services['mdblist'] = {'api_key': api_key}
        self._save_services()
        self.log('MDBList API key saved')
    
    def authenticate_mdblist(self):
        """Prompt user for MDBList API key."""
        api_key = self.dialog.input(
            'MDBList API Key',
            defaultt=self.get_mdblist_key() or '',
            type=xbmcgui.INPUT_ALPHANUM
        )
        
        if api_key:
            self.save_mdblist_key(api_key)
            self.dialog.notification(ADDON_NAME, 'MDBList מוגדר!', xbmcgui.NOTIFICATION_INFO)
            return True
        return False
    
    # =========================================================================
    # PREMIUMIZE
    # =========================================================================
    
    def check_premiumize_status(self):
        """Check if Premiumize is authenticated."""
        return 'premiumize' in self.services and 'api_key' in self.services['premiumize']
    
    def get_premiumize_key(self):
        """Get Premiumize API key."""
        if self.check_premiumize_status():
            return self.services['premiumize'].get('api_key')
        return None
    
    def save_premiumize_key(self, api_key):
        """Save Premiumize API key."""
        self.services['premiumize'] = {'api_key': api_key}
        self._save_services()
        self.log('Premiumize API key saved')
    
    def authenticate_premiumize(self):
        """Prompt user for Premiumize API key."""
        self.dialog.ok(
            'Premiumize',
            '[COLOR cyan]לקבלת API Key:[/COLOR]\n\n'
            '1. היכנס ל-premiumize.me\n'
            '2. לך להגדרות חשבון\n'
            '3. העתק את ה-API Key'
        )
        
        api_key = self.dialog.input(
            'Premiumize API Key',
            defaultt=self.get_premiumize_key() or '',
            type=xbmcgui.INPUT_ALPHANUM
        )
        
        if api_key:
            self.save_premiumize_key(api_key)
            self.dialog.notification(ADDON_NAME, 'Premiumize מחובר!', xbmcgui.NOTIFICATION_INFO)
            return True
        return False
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def configure_all_services(self):
        """Configure all authenticated services in compatible addons."""
        self._configure_rd_in_addons()
        # Add more addon configurations as needed
    
    def get_service_status(self):
        """Get status of all services."""
        return {
            'real_debrid': {
                'connected': self.check_real_debrid_status(),
                'priority': RD_PRIORITY,
            },
            'trakt': {
                'connected': self.check_trakt_status(),
            },
            'mdblist': {
                'connected': self.check_mdblist_status(),
            },
            'premiumize': {
                'connected': self.check_premiumize_status(),
            },
        }
    
    def revoke_service(self, service_name):
        """Revoke a service authentication."""
        if service_name in self.services:
            del self.services[service_name]
            self._save_services()
            self.log(f'Revoked service: {service_name}')
            return True
        return False


# Convenience functions
def check_real_debrid_status():
    return ServiceAuth().check_real_debrid_status()

def check_trakt_status():
    return ServiceAuth().check_trakt_status()

def check_mdblist_status():
    return ServiceAuth().check_mdblist_status()

def check_premiumize_status():
    return ServiceAuth().check_premiumize_status()

def authenticate_real_debrid():
    return ServiceAuth().authenticate_real_debrid()

def authenticate_trakt():
    return ServiceAuth().authenticate_trakt()

def save_mdblist_key(api_key):
    ServiceAuth().save_mdblist_key(api_key)

def save_premiumize_key(api_key):
    ServiceAuth().save_premiumize_key(api_key)

def configure_all_services():
    ServiceAuth().configure_all_services()
