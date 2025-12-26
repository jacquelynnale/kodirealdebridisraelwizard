# -*- coding: utf-8 -*-
"""
Israel Wizard - ישראל וויזארד
Professional Israeli Kodi Wizard with Real Debrid Support
Kodi 21 Omega Compatible

Copyright (C) 2024 Israel Kodi Community
SPDX-License-Identifier: GPL-3.0-only
"""

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import sys
import os
import json
from urllib.parse import parse_qsl, urlencode

# Import wizard library modules
try:
    from resources.lib import wizard_core
    from resources.lib import repo_manager
    from resources.lib import addon_installer
    from resources.lib import service_auth
    from resources.lib import backup_restore
    from resources.lib import ui_builder
except ImportError:
    # Fallback for development
    pass

# =============================================================================
# CONSTANTS
# =============================================================================

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_DATA = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
ADDON_ICON = os.path.join(ADDON_PATH, 'resources', 'icon.png')
ADDON_FANART = os.path.join(ADDON_PATH, 'resources', 'fanart.jpg')

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL = sys.argv[0] if sys.argv else ''

# Theme Colors (Arctic Zephyr Inspired)
COLOR_BACKGROUND = 'FF000000'  # #000000
COLOR_SECONDARY = 'FF171717'   # #171717
COLOR_ACCENT = 'FF0066CC'      # #0066CC
COLOR_SUCCESS = 'FF00CC66'     # Green
COLOR_WARNING = 'FFCC6600'     # Orange
COLOR_ERROR = 'FFCC0000'       # Red

# =============================================================================
# HEBREW STRINGS (RTL Support)
# =============================================================================

STRINGS = {
    'main_menu': 'Main Menu',
    'install_wizard': 'Install Wizard',
    'fresh_install': 'Fresh Install',
    'full_install': 'Full Install',
    'install_repos': 'Install Repositories',
    'install_addons': 'Install Addons',
    'my_services': 'My Services',
    'real_debrid': 'Real Debrid',
    'trakt': 'Trakt',
    'mdblist': 'MDBList',
    'premiumize': 'Premiumize',
    'backup_restore': 'Backup & Restore',
    'backup': 'Backup',
    'restore': 'Restore',
    'settings': 'Settings',
    'about': 'About',
    
    # Menu Items
    'movies': 'Movies',
    'my_movies': 'My Movies',
    'tv_series': 'TV Series',
    'israeli_tv': 'Israeli TV',
    'israeli_content': 'Israeli Content',
    'favorites': 'Favorites',
    'pov': 'POV',
    
    # Status Messages
    'installing': 'Installing...',
    'success': 'Success!',
    'failed': 'Failed',
    'connected': 'Connected ✓',
    'not_connected': 'Not Connected',
    'authorize': 'Authorize',
    'please_wait': 'Please Wait...',
    
    # Dialogs
    'confirm_install': 'Do you want to install this build?',
    'confirm_restore': 'Do you want to restore this backup?',
    'restart_required': 'Kodi restart is required',
    'restart_now': 'Restart now?',
}


def get_string(key):
    """Get localized string with RTL support."""
    return STRINGS.get(key, key)


# =============================================================================
# MENU BUILDERS
# =============================================================================

def build_url(**kwargs):
    """Build plugin URL with parameters."""
    return f'{BASE_URL}?{urlencode(kwargs)}'


def add_menu_item(label, action, icon=None, fanart=None, description='', 
                  is_folder=True, context_menu=None):
    """Add a menu item with RTL Hebrew support."""
    list_item = xbmcgui.ListItem(label=label)
    
    # Set artwork
    art = {
        'icon': icon or ADDON_ICON,
        'thumb': icon or ADDON_ICON,
        'fanart': fanart or ADDON_FANART,
    }
    list_item.setArt(art)
    
    # Set info
    info_tag = list_item.getVideoInfoTag()
    info_tag.setTitle(label)
    info_tag.setPlot(description)
    
    # Context menu
    if context_menu:
        list_item.addContextMenuItems(context_menu)
    
    url = build_url(action=action)
    xbmcplugin.addDirectoryItem(
        handle=HANDLE,
        url=url,
        listitem=list_item,
        isFolder=is_folder
    )


def show_main_menu():
    """Display the main wizard menu with Hebrew RTL support."""
    xbmcplugin.setPluginCategory(HANDLE, get_string('main_menu'))
    xbmcplugin.setContent(HANDLE, 'files')
    
    # Main menu items with Hebrew labels
    menu_items = [
        {
            'label': f'[COLOR {COLOR_ACCENT}][B]🚀 Install Build[/B][/COLOR]',
            'action': 'install_menu',
            'description': 'Install professional build with all addons and skin',
        },
        {
            'label': f'[COLOR {COLOR_ACCENT}]📦 {get_string("install_repos")}[/COLOR]',
            'action': 'install_repos',
            'description': 'Install all required repositories',
        },
        {
            'label': f'[COLOR {COLOR_ACCENT}]🔌 {get_string("install_addons")}[/COLOR]',
            'action': 'install_addons',
            'description': 'Install video addons, subtitles, and tools',
        },
        {
            'label': f'[COLOR {COLOR_SUCCESS}]⚡ {get_string("my_services")}[/COLOR]',
            'action': 'services_menu',
            'description': 'Connect services: Real Debrid, Trakt, MDBList',
        },
        {
            'label': f'[COLOR {COLOR_WARNING}]💾 {get_string("backup_restore")}[/COLOR]',
            'action': 'backup_menu',
            'description': 'Backup and Restore Kodi settings',
        },
        {
            'label': f'⚙️ {get_string("settings")}',
            'action': 'settings',
            'description': 'Wizard Settings',
        },
        {
            'label': f'ℹ️ {get_string("about")}',
            'action': 'about',
            'description': 'About Israel Wizard',
        },
    ]
    
    for item in menu_items:
        add_menu_item(
            label=item['label'],
            action=item['action'],
            description=item['description'],
            is_folder=item['action'] not in ['settings', 'about']
        )
    
    xbmcplugin.endOfDirectory(HANDLE)


def show_install_menu():
    """Display build installation options."""
    xbmcplugin.setPluginCategory(HANDLE, 'התקנת בילד')
    xbmcplugin.setContent(HANDLE, 'files')
    
    install_items = [
        {
            'label': f'[COLOR {COLOR_SUCCESS}][B]🌟 Full Build[/B][/COLOR]',
            'action': 'install_full',
            'description': 'Full installation with all addons, skin, and widgets',
        },
        {
            'label': f'[COLOR {COLOR_ACCENT}]✨ Fresh Build[/COLOR]',
            'action': 'install_fresh',
            'description': 'Fresh installation with essential addons only',
        },
        {
            'label': f'[COLOR {COLOR_WARNING}]🔧 Custom Install[/COLOR]',
            'action': 'install_custom',
            'description': 'Choose which components to install',
        },
    ]
    
    for item in install_items:
        add_menu_item(
            label=item['label'],
            action=item['action'],
            description=item['description'],
            is_folder=False
        )
    
    xbmcplugin.endOfDirectory(HANDLE)


def show_services_menu():
    """Display services authentication menu."""
    xbmcplugin.setPluginCategory(HANDLE, get_string('my_services'))
    xbmcplugin.setContent(HANDLE, 'files')
    
    # Check service status
    rd_status = service_auth.check_real_debrid_status() if 'service_auth' in dir() else False
    trakt_status = service_auth.check_trakt_status() if 'service_auth' in dir() else False
    mdb_status = service_auth.check_mdblist_status() if 'service_auth' in dir() else False
    pm_status = service_auth.check_premiumize_status() if 'service_auth' in dir() else False
    
    def status_icon(connected):
        return f'[COLOR {COLOR_SUCCESS}]✓[/COLOR]' if connected else f'[COLOR {COLOR_ERROR}]✗[/COLOR]'
    
    services = [
        {
            'label': f'{status_icon(rd_status)} [B]Real Debrid[/B] - Priority 90',
            'action': 'auth_realdebrid',
            'description': 'Connect Real Debrid for high quality streaming',
        },
        {
            'label': f'{status_icon(trakt_status)} [B]Trakt[/B]',
            'action': 'auth_trakt',
            'description': 'Sync lists and scrobbling with Trakt',
        },
        {
            'label': f'{status_icon(mdb_status)} [B]MDBList[/B]',
            'action': 'auth_mdblist',
            'description': 'Custom lists from MDBList',
        },
        {
            'label': f'{status_icon(pm_status)} [B]Premiumize[/B]',
            'action': 'auth_premiumize',
            'description': 'Premiumize connection',
        },
    ]
    
    for svc in services:
        add_menu_item(
            label=svc['label'],
            action=svc['action'],
            description=svc['description'],
            is_folder=False
        )
    
    xbmcplugin.endOfDirectory(HANDLE)


def show_backup_menu():
    """Display backup and restore options."""
    xbmcplugin.setPluginCategory(HANDLE, get_string('backup_restore'))
    xbmcplugin.setContent(HANDLE, 'files')
    
    backup_items = [
        {
            'label': f'[COLOR {COLOR_SUCCESS}]💾 {get_string("backup")} - Create Backup[/COLOR]',
            'action': 'create_backup',
            'description': 'Full backup of addons, settings, and skin',
        },
        {
            'label': f'[COLOR {COLOR_WARNING}]📥 {get_string("restore")} - Restore Backup[/COLOR]',
            'action': 'restore_backup',
            'description': 'Restore from previous backup',
        },
        {
            'label': f'[COLOR {COLOR_ERROR}]🗑️ Clear Cache[/COLOR]',
            'action': 'clear_cache',
            'description': 'Clear temp files and cache',
        },
    ]
    
    for item in backup_items:
        add_menu_item(
            label=item['label'],
            action=item['action'],
            description=item['description'],
            is_folder=False
        )
    
    xbmcplugin.endOfDirectory(HANDLE)


# =============================================================================
# ACTION HANDLERS
# =============================================================================

def install_full_build():
    """Install the full featured build."""
    dialog = xbmcgui.Dialog()
    
    if not dialog.yesno(
        ADDON_NAME,
    if not dialog.yesno(
        ADDON_NAME,
        'Install Full Build?\n\nThis will replace your current settings.',
        yeslabel='Install',
        nolabel='Cancel'
    ):...
    
    # ... (other dialogs similarly updated in subsequent replaced lines or manually if complex)

    dialog.textviewer(
        f'{ADDON_NAME} v{ADDON_VERSION}',
        '''[COLOR cyan][B]Israel Wizard[/B][/COLOR]

Version: {ADDON_VERSION}
Compatible: Kodi 21 Omega

[COLOR yellow]Features:[/COLOR]
• Auto-install addons and repositories
• Full Real Debrid integration
• Support for Trakt, MDBList, Premiumize
• English interface
• Optimized for Firestick/Android TV
• Backup & Restore

[COLOR green]Credits:[/COLOR]
Israel Kodi Community
OpenWizard Framework

[COLOR red]Disclaimer:[/COLOR]
This wizard is for legal use only.
Please ensure you have rights to view content.

[COLOR cyan]GitHub:[/COLOR]
github.com/israelwizard/kodirealdebridisraelwizard

[COLOR cyan]Telegram:[/COLOR]
t.me/israelkodi'''
    )
    ):
        return
    
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, 'מתחיל התקנה...')
    
    try:
        # Step 1: Install repositories
        progress.update(10, 'מתקין מאגרים...')
        if 'repo_manager' in dir():
            repo_manager.install_all_repos(progress_callback=lambda p, m: progress.update(10 + int(p * 0.2), m))
        
        # Step 2: Install addons
        progress.update(30, 'מתקין תוספים...')
        if 'addon_installer' in dir():
            addon_installer.install_all_addons(progress_callback=lambda p, m: progress.update(30 + int(p * 0.3), m))
        
        # Step 3: Configure services
        progress.update(60, 'מגדיר שירותים...')
        if 'service_auth' in dir():
            service_auth.configure_all_services()
        
        # Step 4: Apply skin and settings
        progress.update(80, 'מחיל עיצוב והגדרות...')
        if 'ui_builder' in dir():
            ui_builder.apply_skin_settings()
        
        # Step 5: Apply guisettings
        progress.update(95, 'מסיים...')
        apply_guisettings()
        
        progress.close()
        
        # Success dialog
        if dialog.yesno(
            ADDON_NAME,
            '[COLOR green]ההתקנה הושלמה בהצלחה![/COLOR]\n\nיש לאתחל את קודי כדי להחיל את השינויים.',
            yeslabel='אתחל עכשיו',
            nolabel='מאוחר יותר'
        ):
            xbmc.executebuiltin('Quit')
            
    except Exception as e:
        progress.close()
        dialog.notification(ADDON_NAME, f'שגיאה: {str(e)}', xbmcgui.NOTIFICATION_ERROR)
        xbmc.log(f'{ADDON_ID}: Install error - {str(e)}', xbmc.LOGERROR)


def install_fresh_build():
    """Install fresh/minimal build."""
    dialog = xbmcgui.Dialog()
    
    if not dialog.yesno(
        ADDON_NAME,
        'האם להתקין בילד נקי?\n\nזה יתקין רק את התוספים הבסיסיים.',
        yeslabel='התקן',
        nolabel='ביטול'
    ):
        return
    
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, 'מתחיל התקנה נקייה...')
    
    try:
        # Install only essential repos and addons
        progress.update(20, 'מתקין מאגרים בסיסיים...')
        if 'repo_manager' in dir():
            repo_manager.install_essential_repos()
        
        progress.update(50, 'מתקין תוספים בסיסיים...')
        if 'addon_installer' in dir():
            addon_installer.install_essential_addons()
        
        progress.update(100, 'הושלם!')
        progress.close()
        
        dialog.notification(ADDON_NAME, 'התקנה נקייה הושלמה!', xbmcgui.NOTIFICATION_INFO)
        
    except Exception as e:
        progress.close()
        dialog.notification(ADDON_NAME, f'שגיאה: {str(e)}', xbmcgui.NOTIFICATION_ERROR)


def install_repos():
    """Install all repositories."""
    if 'repo_manager' in dir():
        repo_manager.install_all_repos_interactive()
    else:
        xbmcgui.Dialog().notification(ADDON_NAME, 'מודול מאגרים לא נמצא', xbmcgui.NOTIFICATION_ERROR)


def install_addons():
    """Install all addons."""
    if 'addon_installer' in dir():
        addon_installer.install_all_addons_interactive()
    else:
        xbmcgui.Dialog().notification(ADDON_NAME, 'מודול תוספים לא נמצא', xbmcgui.NOTIFICATION_ERROR)


def auth_real_debrid():
    """Authenticate with Real Debrid."""
    dialog = xbmcgui.Dialog()
    
    # Display auth instructions
    dialog.ok(
        'Real Debrid',
        '[COLOR cyan]לחיבור Real Debrid:[/COLOR]\n\n'
        '1. פתח את real-debrid.com/device\n'
        '2. הזן את הקוד שיופיע\n'
        '3. אשר את החיבור'
    )
    
    if 'service_auth' in dir():
        success = service_auth.authenticate_real_debrid()
        if success:
            dialog.notification(ADDON_NAME, 'Real Debrid מחובר!', xbmcgui.NOTIFICATION_INFO)
        else:
            dialog.notification(ADDON_NAME, 'חיבור נכשל', xbmcgui.NOTIFICATION_ERROR)
    else:
        # Simulate for demo
        import webbrowser
        try:
            webbrowser.open('https://real-debrid.com/device')
        except:
            pass
        dialog.notification(ADDON_NAME, 'פתח real-debrid.com/device', xbmcgui.NOTIFICATION_INFO)


def auth_trakt():
    """Authenticate with Trakt."""
    dialog = xbmcgui.Dialog()
    
    dialog.ok(
        'Trakt',
        '[COLOR cyan]לחיבור Trakt:[/COLOR]\n\n'
        '1. פתח את trakt.tv/activate\n'
        '2. הזן את הקוד שיופיע\n'
        '3. אשר את החיבור'
    )
    
    if 'service_auth' in dir():
        success = service_auth.authenticate_trakt()
        if success:
            dialog.notification(ADDON_NAME, 'Trakt מחובר!', xbmcgui.NOTIFICATION_INFO)


def auth_mdblist():
    """Setup MDBList API."""
    dialog = xbmcgui.Dialog()
    
    api_key = dialog.input(
        'MDBList API Key',
        type=xbmcgui.INPUT_ALPHANUM
    )
    
    if api_key:
        if 'service_auth' in dir():
            service_auth.save_mdblist_key(api_key)
        dialog.notification(ADDON_NAME, 'MDBList מוגדר!', xbmcgui.NOTIFICATION_INFO)


def auth_premiumize():
    """Authenticate with Premiumize."""
    dialog = xbmcgui.Dialog()
    
    dialog.ok(
        'Premiumize',
        '[COLOR cyan]לחיבור Premiumize:[/COLOR]\n\n'
        '1. פתח את premiumize.me\n'
        '2. היכנס לחשבון שלך\n'
        '3. העתק את ה-API Key'
    )
    
    api_key = dialog.input(
        'Premiumize API Key',
        type=xbmcgui.INPUT_ALPHANUM
    )
    
    if api_key:
        if 'service_auth' in dir():
            service_auth.save_premiumize_key(api_key)
        dialog.notification(ADDON_NAME, 'Premiumize מחובר!', xbmcgui.NOTIFICATION_INFO)


def create_backup():
    """Create a backup of Kodi settings."""
    if 'backup_restore' in dir():
        backup_restore.create_backup_interactive()
    else:
        dialog = xbmcgui.Dialog()
        dialog.notification(ADDON_NAME, 'מודול גיבוי לא נמצא', xbmcgui.NOTIFICATION_ERROR)


def restore_backup():
    """Restore from a backup."""
    if 'backup_restore' in dir():
        backup_restore.restore_backup_interactive()
    else:
        dialog = xbmcgui.Dialog()
        dialog.notification(ADDON_NAME, 'מודול גיבוי לא נמצא', xbmcgui.NOTIFICATION_ERROR)


def clear_cache():
    """Clear Kodi cache."""
    dialog = xbmcgui.Dialog()
    
    if dialog.yesno(ADDON_NAME, 'האם לנקות את המטמון?'):
        # Clear cache directories
        cache_paths = [
            xbmcvfs.translatePath('special://temp/'),
            xbmcvfs.translatePath('special://home/cache/'),
        ]
        
        cleared = 0
        for path in cache_paths:
            if xbmcvfs.exists(path):
                dirs, files = xbmcvfs.listdir(path)
                for f in files:
                    try:
                        xbmcvfs.delete(os.path.join(path, f))
                        cleared += 1
                    except:
                        pass
        
        dialog.notification(ADDON_NAME, f'נוקו {cleared} קבצים', xbmcgui.NOTIFICATION_INFO)


def apply_guisettings():
    """Apply custom GUI settings for the wizard skin."""
    guisettings_path = os.path.join(ADDON_PATH, 'guisettings', 'guisettings.xml')
    
    if os.path.exists(guisettings_path):
        target_path = xbmcvfs.translatePath('special://userdata/guisettings.xml')
        try:
            xbmcvfs.copy(guisettings_path, target_path)
            xbmc.log(f'{ADDON_ID}: Applied guisettings.xml', xbmc.LOGINFO)
            return True
        except Exception as e:
            xbmc.log(f'{ADDON_ID}: Failed to apply guisettings - {str(e)}', xbmc.LOGERROR)
            return False
    return False


def show_settings():
    """Open addon settings."""
    ADDON.openSettings()


def show_about():
    """Show about dialog."""
    dialog = xbmcgui.Dialog()
    dialog.textviewer(
        f'{ADDON_NAME} v{ADDON_VERSION}',
        '''[COLOR cyan][B]ישראל וויזארד - Israel Wizard[/B][/COLOR]

גרסה: 1.0.0
תואם: Kodi 21 Omega

[COLOR yellow]תכונות:[/COLOR]
• התקנה אוטומטית של תוספים ומאגרים
• אינטגרציה מלאה עם Real Debrid
• תמיכה ב-Trakt, MDBList, Premiumize
• ממשק עברי מלא עם תמיכה RTL
• אופטימיזציה ל-Firestick/Android TV
• גיבוי ושחזור

[COLOR green]קרדיטים:[/COLOR]
Israel Kodi Community
OpenWizard Framework

[COLOR red]הבהרה:[/COLOR]
האשף הזה מיועד לשימוש חוקי בלבד.
אנא ודא שיש לך זכויות לצפות בתוכן.

[COLOR cyan]GitHub:[/COLOR]
github.com/israelwizard/kodirealdebridisraelwizard

[COLOR cyan]Telegram:[/COLOR]
t.me/israelkodi'''
    )


# =============================================================================
# ROUTER
# =============================================================================

def router(paramstring):
    """Route plugin calls to appropriate functions."""
    params = dict(parse_qsl(paramstring))
    action = params.get('action', '')
    
    if not action:
        show_main_menu()
    elif action == 'install_menu':
        show_install_menu()
    elif action == 'install_full':
        install_full_build()
    elif action == 'install_fresh':
        install_fresh_build()
    elif action == 'install_custom':
        show_install_menu()  # TODO: Custom install wizard
    elif action == 'install_repos':
        install_repos()
    elif action == 'install_addons':
        install_addons()
    elif action == 'services_menu':
        show_services_menu()
    elif action == 'auth_realdebrid':
        auth_real_debrid()
    elif action == 'auth_trakt':
        auth_trakt()
    elif action == 'auth_mdblist':
        auth_mdblist()
    elif action == 'auth_premiumize':
        auth_premiumize()
    elif action == 'backup_menu':
        show_backup_menu()
    elif action == 'create_backup':
        create_backup()
    elif action == 'restore_backup':
        restore_backup()
    elif action == 'clear_cache':
        clear_cache()
    elif action == 'settings':
        show_settings()
    elif action == 'about':
        show_about()
    else:
        show_main_menu()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    router(sys.argv[2][1:] if len(sys.argv) > 2 else '')
