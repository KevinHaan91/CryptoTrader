import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import hmac
import hashlib
import time

logger = logging.getLogger(__name__)

class ExchangeMonitor:
    """Monitor centralized exchanges for new listings"""
    
    def __init__(self, exchange_credentials: Dict = None):
        self.credentials = exchange_credentials or {}
        self.session = None
        
        # Exchange configurations
        self.exchanges = {
            'mexc': {
                'api_url': 'https://api.mexc.com/api/v3',
                'announcement_url': 'https://support.mexc.com/hc/en-001/sections/announcements',
                'websocket': 'wss://wbs.mexc.com/ws',
                'check_interval': 300  # 5 minutes
            },
            'kucoin': {
                'api_url': 'https://api.kucoin.com/api/v1',
                'announcement_url': 'https://www.kucoin.com/news/categories/listing',
                'websocket': 'wss://ws-api.kucoin.com/endpoint',
                'check_interval': 300
            },
            'gate': {
                'api_url': 'https://api.gateio.ws/api/v4',
                'announcement_url': 'https://www.gate.io/en/article',
                'check_interval': 300
            },
            'binance': {
                'api_url': 'https://api.binance.com/api/v3',
                'announcement_url': 'https://www.binance.com/en/support/announcement/new-cryptocurrency-listing',
                'websocket': 'wss://stream.binance.com:9443/ws',
                'check_interval': 600  # 10 minutes
            },
            'bybit': {
                'api_url': 'https://api.bybit.com/v5',
                'announcement_url': 'https://announcements.bybit.com/en-US/',
                'check_interval': 300
            }
        }
        
        # Track listings
        self.known_pairs = {}  # exchange -> set of trading pairs
        self.new_listings = []  # Recent new listings
        self.listing_alerts = set()  # Prevent duplicate alerts
        
        # Pre-listing tracking
        self.announcement_cache = {}
        self.pending_listings = {}  # Tokens announced but not yet trading
        
    async def start_monitoring(self):
        """Start monitoring exchanges"""
        self.session = aiohttp.ClientSession()
        
        # Initialize known pairs
        await self._initialize_known_pairs()
        
        # Start monitoring tasks
        tasks = []
        for exchange in self.exchanges:
            tasks.append(asyncio.create_task(self._monitor_exchange(exchange)))
        
        await asyncio.gather(*tasks)
    
    async def _initialize_known_pairs(self):
        """Get current trading pairs for each exchange"""
        for exchange in self.exchanges:
            try:
                pairs = await self._get_trading_pairs(exchange)
                self.known_pairs[exchange] = set(pairs)
                logger.info(f"Initialized {exchange} with {len(pairs)} pairs")
            except Exception as e:
                logger.error(f"Error initializing {exchange}: {e}")
                self.known_pairs[exchange] = set()
    
    async def _monitor_exchange(self, exchange: str):
        """Monitor specific exchange for new listings"""
        config = self.exchanges[exchange]
        
        while True:
            try:
                # Check for new announcements
                new_announcements = await self._check_announcements(exchange)
                
                for announcement in new_announcements:
                    await self._process_announcement(exchange, announcement)
                
                # Check for new trading pairs
                current_pairs = await self._get_trading_pairs(exchange)
                
                if current_pairs:
                    new_pairs = set(current_pairs) - self.known_pairs.get(exchange, set())
                    
                    for pair in new_pairs:
                        await self._process_new_listing(exchange, pair)
                    
                    self.known_pairs[exchange] = set(current_pairs)
                
                await asyncio.sleep(config['check_interval'])
                
            except Exception as e:
                logger.error(f"Error monitoring {exchange}: {e}")
                await asyncio.sleep(config['check_interval'])
    
    async def _get_trading_pairs(self, exchange: str) -> List[str]:
        """Get all trading pairs from exchange"""
        try:
            if exchange == 'mexc':
                return await self._get_mexc_pairs()
            elif exchange == 'kucoin':
                return await self._get_kucoin_pairs()
            elif exchange == 'gate':
                return await self._get_gate_pairs()
            elif exchange == 'binance':
                return await self._get_binance_pairs()
            elif exchange == 'bybit':
                return await self._get_bybit_pairs()
        except Exception as e:
            logger.error(f"Error getting pairs from {exchange}: {e}")
        
        return []
    
    async def _get_mexc_pairs(self) -> List[str]:
        """Get MEXC trading pairs"""
        url = f"{self.exchanges['mexc']['api_url']}/exchangeInfo"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                pairs = []
                for symbol_info in data.get('symbols', []):
                    if symbol_info['status'] == 'TRADING':
                        pairs.append(symbol_info['symbol'])
                
                return pairs
        
        return []
    
    async def _get_kucoin_pairs(self) -> List[str]:
        """Get KuCoin trading pairs"""
        url = f"{self.exchanges['kucoin']['api_url']}/symbols"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get('code') == '200000':
                    pairs = []
                    for symbol in data.get('data', []):
                        if symbol.get('enableTrading'):
                            pairs.append(symbol['symbol'])
                    
                    return pairs
        
        return []
    
    async def _get_gate_pairs(self) -> List[str]:
        """Get Gate.io trading pairs"""
        url = f"{self.exchanges['gate']['api_url']}/spot/currency_pairs"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                pairs = []
                for pair in data:
                    if pair.get('trade_status') == 'tradable':
                        pairs.append(pair['id'])
                
                return pairs
        
        return []
    
    async def _get_binance_pairs(self) -> List[str]:
        """Get Binance trading pairs"""
        url = f"{self.exchanges['binance']['api_url']}/exchangeInfo"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                pairs = []
                for symbol in data.get('symbols', []):
                    if symbol['status'] == 'TRADING':
                        pairs.append(symbol['symbol'])
                
                return pairs
        
        return []
    
    async def _get_bybit_pairs(self) -> List[str]:
        """Get Bybit trading pairs"""
        url = f"{self.exchanges['bybit']['api_url']}/market/instruments-info"
        params = {'category': 'spot'}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get('retCode') == 0:
                    pairs = []
                    for instrument in data.get('result', {}).get('list', []):
                        if instrument.get('status') == 'Trading':
                            pairs.append(instrument['symbol'])
                    
                    return pairs
        
        return []
    
    async def _check_announcements(self, exchange: str) -> List[Dict]:
        """Check for new listing announcements"""
        try:
            url = self.exchanges[exchange]['announcement_url']
            
            # Get cached announcements
            cached = self.announcement_cache.get(exchange, [])
            cached_ids = {ann.get('id') for ann in cached}
            
            # Fetch current announcements
            announcements = await self._fetch_announcements(exchange, url)
            
            # Find new ones
            new_announcements = []
            for ann in announcements:
                if ann.get('id') not in cached_ids:
                    # Check if it's a listing announcement
                    if self._is_listing_announcement(ann):
                        new_announcements.append(ann)
            
            # Update cache
            self.announcement_cache[exchange] = announcements[:50]  # Keep last 50
            
            return new_announcements
            
        except Exception as e:
            logger.error(f"Error checking {exchange} announcements: {e}")
            return []
    
    async def _fetch_announcements(self, exchange: str, url: str) -> List[Dict]:
        """Fetch announcements from exchange"""
        announcements = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    if exchange == 'mexc':
                        announcements = await self._parse_mexc_announcements(response)
                    elif exchange == 'kucoin':
                        announcements = await self._parse_kucoin_announcements(response)
                    elif exchange == 'binance':
                        announcements = await self._parse_binance_announcements(response)
                    else:
                        # Generic parsing
                        html = await response.text()
                        announcements = self._parse_generic_announcements(html, exchange)
        
        except Exception as e:
            logger.error(f"Error fetching {exchange} announcements: {e}")
        
        return announcements
    
    async def _parse_mexc_announcements(self, response) -> List[Dict]:
        """Parse MEXC announcements"""
        announcements = []
        
        try:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find announcement articles
            articles = soup.find_all('article', class_='announcement-item')
            
            for article in articles[:20]:  # Last 20 announcements
                try:
                    title = article.find('h3').text.strip()
                    link = article.find('a')['href']
                    date_str = article.find('time').text.strip()
                    
                    announcements.append({
                        'id': link,
                        'title': title,
                        'url': f"https://support.mexc.com{link}",
                        'date': date_str,
                        'content': ''
                    })
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing MEXC announcements: {e}")
        
        return announcements
    
    async def _parse_kucoin_announcements(self, response) -> List[Dict]:
        """Parse KuCoin announcements via API"""
        announcements = []
        
        try:
            # KuCoin has API for announcements
            api_url = "https://www.kucoin.com/_api/cms/articles"
            params = {
                'page': 1,
                'pageSize': 20,
                'category': 'listing'
            }
            
            async with self.session.get(api_url, params=params) as api_response:
                if api_response.status == 200:
                    data = await api_response.json()
                    
                    for item in data.get('items', []):
                        announcements.append({
                            'id': item['id'],
                            'title': item['title'],
                            'url': f"https://www.kucoin.com/news/{item['id']}",
                            'date': item['publishedAt'],
                            'content': item.get('summary', '')
                        })
                        
        except Exception as e:
            logger.error(f"Error parsing KuCoin announcements: {e}")
        
        return announcements
    
    async def _parse_binance_announcements(self, response) -> List[Dict]:
        """Parse Binance announcements"""
        announcements = []
        
        try:
            # Binance uses API for announcements
            api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
            
            payload = {
                "type": 1,
                "catalogId": 48,  # New listings category
                "pageNo": 1,
                "pageSize": 20
            }
            
            async with self.session.post(api_url, json=payload) as api_response:
                if api_response.status == 200:
                    data = await api_response.json()
                    
                    for article in data.get('data', {}).get('articles', []):
                        announcements.append({
                            'id': article['id'],
                            'title': article['title'],
                            'url': f"https://www.binance.com/en/support/announcement/{article['code']}",
                            'date': article['releaseDate'],
                            'content': article.get('brief', '')
                        })
                        
        except Exception as e:
            logger.error(f"Error parsing Binance announcements: {e}")
        
        return announcements
    
    def _parse_generic_announcements(self, html: str, exchange: str) -> List[Dict]:
        """Generic announcement parsing"""
        announcements = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Common patterns for announcements
        patterns = [
            {'tag': 'article', 'class': 'announcement'},
            {'tag': 'div', 'class': 'news-item'},
            {'tag': 'li', 'class': 'article'},
            {'tag': 'div', 'class': 'list-item'}
        ]
        
        for pattern in patterns:
            items = soup.find_all(pattern['tag'], class_=pattern['class'])
            
            if items:
                for item in items[:20]:
                    try:
                        # Extract title
                        title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                        if not title_elem:
                            continue
                        
                        title = title_elem.text.strip()
                        
                        # Extract link
                        link_elem = item.find('a')
                        link = link_elem['href'] if link_elem else ''
                        
                        announcements.append({
                            'id': link or title,
                            'title': title,
                            'url': link,
                            'date': datetime.now().isoformat(),
                            'content': ''
                        })
                    except:
                        continue
                
                break
        
        return announcements
    
    def _is_listing_announcement(self, announcement: Dict) -> bool:
        """Check if announcement is about new listing"""
        title = announcement.get('title', '').lower()
        content = announcement.get('content', '').lower()
        
        # Keywords indicating new listing
        listing_keywords = [
            'will list', 'lists', 'listing', 'new trading',
            'trading pair', 'launches', 'addition',
            'adds', 'introduces', 'now available',
            'trading enabled', 'spot trading', 'perpetual'
        ]
        
        # Check title and content
        text = f"{title} {content}"
        
        return any(keyword in text for keyword in listing_keywords)
    
    async def _process_announcement(self, exchange: str, announcement: Dict):
        """Process new listing announcement"""
        try:
            # Extract token information
            tokens = self._extract_tokens_from_announcement(announcement)
            
            for token in tokens:
                # Check if already alerted
                alert_id = f"{exchange}_{token['symbol']}_announcement"
                if alert_id in self.listing_alerts:
                    continue
                
                # Get listing time
                listing_time = self._extract_listing_time(announcement)
                
                # Store pending listing
                self.pending_listings[token['symbol']] = {
                    'exchange': exchange,
                    'symbol': token['symbol'],
                    'name': token.get('name', ''),
                    'announcement': announcement,
                    'announcement_time': datetime.now(),
                    'listing_time': listing_time,
                    'status': 'announced'
                }
                
                self.listing_alerts.add(alert_id)
                
                logger.info(
                    f"New listing announcement on {exchange}: "
                    f"{token['symbol']} - {announcement['title']}"
                )
                
        except Exception as e:
            logger.error(f"Error processing announcement: {e}")
    
    def _extract_tokens_from_announcement(self, announcement: Dict) -> List[Dict]:
        """Extract token symbols from announcement"""
        tokens = []
        
        text = f"{announcement.get('title', '')} {announcement.get('content', '')}"
        
        # Pattern to find token symbols (usually in parentheses or all caps)
        import re
        
        # Find patterns like "Token (TKN)" or "TKN/USDT"
        patterns = [
            r'\(([A-Z]{2,10})\)',  # Symbols in parentheses
            r'([A-Z]{2,10})/USDT',  # Trading pairs
            r'([A-Z]{2,10})/BTC',
            r'([A-Z]{2,10})/ETH',
            r'([A-Z]{2,10})/BUSD',
            r'\b([A-Z]{2,10})\b(?:\s+token|\s+coin|\s+listing)'  # Standalone symbols
        ]
        
        found_symbols = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            found_symbols.update(matches)
        
        # Filter out common words that might match
        exclude = {'THE', 'NEW', 'NOW', 'AND', 'FOR', 'WITH', 'THIS', 'WILL', 'USD', 'USDT', 'BTC', 'ETH'}
        
        for symbol in found_symbols:
            if symbol not in exclude and len(symbol) >= 2:
                tokens.append({
                    'symbol': symbol,
                    'name': self._extract_token_name(text, symbol)
                })
        
        return tokens
    
    def _extract_token_name(self, text: str, symbol: str) -> str:
        """Try to extract token name from text"""
        import re
        
        # Look for patterns like "TokenName (TKN)"
        pattern = rf'([\w\s]+)\s*\({symbol}\)'
        match = re.search(pattern, text)
        
        if match:
            return match.group(1).strip()
        
        return ''
    
    def _extract_listing_time(self, announcement: Dict) -> Optional[datetime]:
        """Extract listing time from announcement"""
        text = f"{announcement.get('title', '')} {announcement.get('content', '')}"
        
        import re
        from dateutil import parser
        
        # Common patterns for dates/times
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',  # 2024-03-15 12:00
            r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})',  # 3/15/2024 12:00
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'at\s+(\d{1,2}:\d{2}\s*(?:AM|PM|UTC))',  # at 12:00 UTC
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    return parser.parse(date_str, fuzzy=True)
                except:
                    continue
        
        # If no specific time found, estimate based on exchange patterns
        # Most exchanges list within 24-48 hours of announcement
        return datetime.now() + timedelta(hours=24)
    
    async def _process_new_listing(self, exchange: str, pair: str):
        """Process newly detected trading pair"""
        try:
            # Extract base symbol from pair
            symbol = self._extract_base_symbol(pair)
            
            # Check if already alerted
            alert_id = f"{exchange}_{symbol}_live"
            if alert_id in self.listing_alerts:
                return
            
            # Check if was previously announced
            was_announced = symbol in self.pending_listings
            
            # Get initial trading data
            trading_data = await self._get_initial_trading_data(exchange, pair)
            
            listing = {
                'exchange': exchange,
                'symbol': symbol,
                'pair': pair,
                'detection_time': datetime.now(),
                'was_announced': was_announced,
                'announcement_lead_time': None,
                'initial_price': trading_data.get('price'),
                'initial_volume': trading_data.get('volume'),
                'status': 'live'
            }
            
            if was_announced:
                pending = self.pending_listings[symbol]
                listing['announcement_lead_time'] = (
                    datetime.now() - pending['announcement_time']
                ).total_seconds() / 3600  # hours
                
                # Update pending listing status
                pending['status'] = 'live'
                pending['went_live'] = datetime.now()
            
            self.new_listings.append(listing)
            self.listing_alerts.add(alert_id)
            
            logger.info(
                f"New listing detected on {exchange}: {pair} "
                f"(Announced: {was_announced})"
            )
            
        except Exception as e:
            logger.error(f"Error processing new listing: {e}")
    
    def _extract_base_symbol(self, pair: str) -> str:
        """Extract base symbol from trading pair"""
        # Common quote currencies
        quotes = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB', 'USD', 'EUR']
        
        for quote in quotes:
            if pair.endswith(quote):
                return pair[:-len(quote)]
        
        # If no match, assume everything except last 3-4 chars is base
        return pair[:-4] if len(pair) > 4 else pair
    
    async def _get_initial_trading_data(self, exchange: str, pair: str) -> Dict:
        """Get initial price and volume data"""
        try:
            if exchange == 'mexc':
                return await self._get_mexc_ticker(pair)
            elif exchange == 'kucoin':
                return await self._get_kucoin_ticker(pair)
            elif exchange == 'binance':
                return await self._get_binance_ticker(pair)
            # Add other exchanges as needed
        except Exception as e:
            logger.error(f"Error getting ticker data: {e}")
        
        return {'price': 0, 'volume': 0}
    
    async def _get_mexc_ticker(self, symbol: str) -> Dict:
        """Get MEXC ticker data"""
        url = f"{self.exchanges['mexc']['api_url']}/ticker/24hr"
        params = {'symbol': symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'price': float(data.get('lastPrice', 0)),
                    'volume': float(data.get('volume', 0))
                }
        
        return {'price': 0, 'volume': 0}
    
    async def _get_kucoin_ticker(self, symbol: str) -> Dict:
        """Get KuCoin ticker data"""
        url = f"{self.exchanges['kucoin']['api_url']}/market/stats"
        params = {'symbol': symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('code') == '200000':
                    ticker = data.get('data', {})
                    return {
                        'price': float(ticker.get('last', 0)),
                        'volume': float(ticker.get('vol', 0))
                    }
        
        return {'price': 0, 'volume': 0}
    
    async def _get_binance_ticker(self, symbol: str) -> Dict:
        """Get Binance ticker data"""
        url = f"{self.exchanges['binance']['api_url']}/ticker/24hr"
        params = {'symbol': symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'price': float(data.get('lastPrice', 0)),
                    'volume': float(data.get('volume', 0))
                }
        
        return {'price': 0, 'volume': 0}
    
    def get_pending_listings(self) -> List[Dict]:
        """Get tokens announced but not yet trading"""
        pending = []
        
        for symbol, listing in self.pending_listings.items():
            if listing['status'] == 'announced':
                time_until_listing = None
                if listing['listing_time']:
                    time_until_listing = (
                        listing['listing_time'] - datetime.now()
                    ).total_seconds() / 3600  # hours
                
                pending.append({
                    'symbol': symbol,
                    'exchange': listing['exchange'],
                    'announcement_time': listing['announcement_time'],
                    'estimated_listing_time': listing['listing_time'],
                    'hours_until_listing': time_until_listing,
                    'announcement_url': listing['announcement']['url']
                })
        
        return pending
    
    def get_recent_listings(self, hours: int = 24) -> List[Dict]:
        """Get recent new listings"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for listing in self.new_listings:
            if listing['detection_time'] > cutoff:
                recent.append(listing)
        
        # Sort by detection time (newest first)
        recent.sort(key=lambda x: x['detection_time'], reverse=True)
        
        return recent
    
    def get_exchange_listing_stats(self) -> Dict:
        """Get listing statistics by exchange"""
        stats = {}
        
        for exchange in self.exchanges:
            total_listings = sum(
                1 for l in self.new_listings 
                if l['exchange'] == exchange
            )
            
            announced_listings = sum(
                1 for l in self.new_listings 
                if l['exchange'] == exchange and l['was_announced']
            )
            
            avg_lead_time = 0
            lead_times = [
                l['announcement_lead_time'] 
                for l in self.new_listings 
                if l['exchange'] == exchange and l['announcement_lead_time']
            ]
            
            if lead_times:
                avg_lead_time = sum(lead_times) / len(lead_times)
            
            stats[exchange] = {
                'total_listings': total_listings,
                'announced_percentage': (announced_listings / total_listings * 100) 
                                       if total_listings > 0 else 0,
                'avg_announcement_lead_hours': avg_lead_time,
                'current_pairs': len(self.known_pairs.get(exchange, []))
            }
        
        return stats
    
    async def close(self):
        """Close monitor connections"""
        if self.session:
            await self.session.close()
