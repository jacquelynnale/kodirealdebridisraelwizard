# -*- coding: utf-8 -*-
"""
Israel Wizard - TechNip Scraper
ישראל וויזארד - סורק TechNip

Ethical Real Debrid torrent scraper for Hebrew movies and series.
Uses cached torrents only - no illegal downloading.
"""

import xbmc
import xbmcaddon
import json
import time
import hashlib
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import HTTPError

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')

# Rate limiting
RATE_LIMIT_SECONDS = 2
_last_request_time = 0

# Cache for results
_cache = {}
CACHE_TTL = 3600  # 1 hour


class TechNipScraper:
    """
    Ethical scraper for Hebrew content via Real Debrid.
    Only uses legally cached torrents from RD's CDN.
    """
    
    def __init__(self, rd_token=None):
        self.rd_token = rd_token
        self.rd_api = 'https://api.real-debrid.com/rest/1.0'
    
    def log(self, message, level=xbmc.LOGINFO):
        xbmc.log(f'{ADDON_ID} TechNip: {message}', level)
    
    def _rate_limit(self):
        global _last_request_time
        elapsed = time.time() - _last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        _last_request_time = time.time()
    
    def _cache_key(self, *args):
        return hashlib.md5(str(args).encode()).hexdigest()
    
    def _get_cached(self, key):
        if key in _cache:
            data, timestamp = _cache[key]
            if time.time() - timestamp < CACHE_TTL:
                return data
            del _cache[key]
        return None
    
    def _set_cached(self, key, data):
        _cache[key] = (data, time.time())
    
    def _rd_request(self, endpoint, params=None):
        if not self.rd_token:
            self.log('No RD token configured', xbmc.LOGWARNING)
            return None
        
        self._rate_limit()
        
        try:
            url = f'{self.rd_api}{endpoint}'
            if params:
                url += f'?{urlencode(params)}'
            
            headers = {
                'Authorization': f'Bearer {self.rd_token}',
                'User-Agent': 'Kodi Israel Wizard',
            }
            
            request = Request(url, headers=headers)
            response = urlopen(request, timeout=15)
            return json.loads(response.read().decode('utf-8'))
            
        except HTTPError as e:
            self.log(f'RD API Error {e.code}: {endpoint}', xbmc.LOGERROR)
        except Exception as e:
            self.log(f'RD Request error: {str(e)}', xbmc.LOGERROR)
        return None
    
    def check_cache(self, magnet_hash):
        """Check if a torrent hash is cached on Real Debrid."""
        cache_key = self._cache_key('instant', magnet_hash)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        result = self._rd_request(f'/torrents/instantAvailability/{magnet_hash}')
        if result and magnet_hash in result:
            is_cached = bool(result[magnet_hash].get('rd', []))
            self._set_cached(cache_key, is_cached)
            return is_cached
        return False
    
    def search_hebrew_content(self, query, content_type='movie'):
        """
        Search for Hebrew content.
        Returns list of available cached results.
        """
        cache_key = self._cache_key('search', query, content_type)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        results = []
        hebrew_terms = ['hebrew', 'עברית', 'heb', 'israeli']
        
        self.log(f'Searching: {query} ({content_type})')
        
        # This is a placeholder - actual implementation would use legal APIs
        # For ethical use, only return cached RD content
        
        self._set_cached(cache_key, results)
        return results
    
    def get_stream_link(self, magnet_or_hash):
        """Get direct stream link from cached torrent."""
        if not self.check_cache(magnet_or_hash):
            self.log('Torrent not cached on RD', xbmc.LOGWARNING)
            return None
        
        # Add magnet to RD
        add_result = self._rd_request('/torrents/addMagnet', {'magnet': magnet_or_hash})
        if not add_result or 'id' not in add_result:
            return None
        
        torrent_id = add_result['id']
        
        # Select files
        self._rd_request(f'/torrents/selectFiles/{torrent_id}', {'files': 'all'})
        
        # Get info
        time.sleep(1)
        info = self._rd_request(f'/torrents/info/{torrent_id}')
        if not info:
            return None
        
        # Get unrestricted link
        links = info.get('links', [])
        if links:
            unrestrict = self._rd_request('/unrestrict/link', {'link': links[0]})
            if unrestrict and 'download' in unrestrict:
                return unrestrict['download']
        
        return None


def create_scraper(rd_token=None):
    """Factory function to create scraper instance."""
    return TechNipScraper(rd_token)
