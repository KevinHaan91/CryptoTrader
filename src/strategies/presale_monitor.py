import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

class PresaleMonitor:
    """Monitor and analyze ICO/IDO/IEO presales"""
    
    def __init__(self, ml_models=None):
        self.ml_models = ml_models
        self.session = None
        
        # Presale platforms to monitor
        self.platforms = {
            'coinlaunch': {
                'url': 'https://coinlaunch.space/api/v1/presales',
                'type': 'api'
            },
            'pinksale': {
                'url': 'https://www.pinksale.finance/launchpads',
                'type': 'scrape'
            },
            'dxsale': {
                'url': 'https://dxsale.app/api/presales/active',
                'type': 'api'
            },
            'unicrypt': {
                'url': 'https://app.unicrypt.network/api/launches',
                'type': 'api'
            },
            'polkastarter': {
                'url': 'https://api.polkastarter.com/api/v1/projects',
                'type': 'api'
            },
            'seedify': {
                'url': 'https://launchpad.seedify.fund/api/v1/idos',
                'type': 'api'
            },
            'gamefi': {
                'url': 'https://gamefi.org/api/v1/pools',
                'type': 'api'
            }
        }
        
        # Track monitored presales
        self.active_presales = {}
        self.completed_presales = {}
        self.alerts_sent = set()
        
    async def start_monitoring(self):
        """Start monitoring presale platforms"""
        self.session = aiohttp.ClientSession()
        
        while True:
            try:
                presales = await self._fetch_all_presales()
                new_opportunities = await self._analyze_presales(presales)
                
                for opportunity in new_opportunities:
                    await self._process_opportunity(opportunity)
                
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Presale monitoring error: {e}")
                await asyncio.sleep(1800)
    
    async def _fetch_all_presales(self) -> List[Dict]:
        """Fetch presales from all platforms"""
        all_presales = []
        
        tasks = []
        for platform, config in self.platforms.items():
            if config['type'] == 'api':
                task = self._fetch_api_presales(platform, config['url'])
            else:
                task = self._scrape_presales(platform, config['url'])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_presales.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Platform fetch error: {result}")
        
        return all_presales
    
    async def _fetch_api_presales(self, platform: str, url: str) -> List[Dict]:
        """Fetch presales from API endpoint"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Normalize data format
                    presales = []
                    
                    if platform == 'coinlaunch':
                        for item in data.get('data', []):
                            presales.append(self._normalize_coinlaunch(item))
                    
                    elif platform == 'polkastarter':
                        for item in data.get('projects', []):
                            presales.append(self._normalize_polkastarter(item))
                    
                    elif platform == 'seedify':
                        for item in data.get('idos', []):
                            presales.append(self._normalize_seedify(item))
                    
                    else:
                        # Generic normalization
                        for item in data if isinstance(data, list) else data.get('data', []):
                            presales.append(self._normalize_generic(item, platform))
                    
                    return presales
                    
        except Exception as e:
            logger.error(f"API fetch error for {platform}: {e}")
        
        return []
    
    async def _scrape_presales(self, platform: str, url: str) -> List[Dict]:
        """Scrape presales from website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if platform == 'pinksale':
                        return self._parse_pinksale(soup)
                    
        except Exception as e:
            logger.error(f"Scraping error for {platform}: {e}")
        
        return []
    
    def _normalize_coinlaunch(self, data: Dict) -> Dict:
        """Normalize CoinLaunch data format"""
        return {
            'platform': 'coinlaunch',
            'id': data.get('id'),
            'name': data.get('name'),
            'symbol': data.get('symbol'),
            'description': data.get('description', ''),
            'start_time': self._parse_timestamp(data.get('start_time')),
            'end_time': self._parse_timestamp(data.get('end_time')),
            'hard_cap': float(data.get('hard_cap', 0)),
            'soft_cap': float(data.get('soft_cap', 0)),
            'token_price': float(data.get('price', 0)),
            'total_supply': float(data.get('total_supply', 0)),
            'raised_amount': float(data.get('raised', 0)),
            'participants': int(data.get('participants', 0)),
            'website': data.get('website'),
            'whitepaper': data.get('whitepaper'),
            'social_links': {
                'twitter': data.get('twitter'),
                'telegram': data.get('telegram'),
                'discord': data.get('discord')
            },
            'audit_status': data.get('audit', {}).get('status'),
            'kyc_status': data.get('kyc', False),
            'team_info': data.get('team', []),
            'tokenomics': data.get('tokenomics', {}),
            'vesting': data.get('vesting', {}),
            'listing_info': {
                'exchange': data.get('listing_exchange'),
                'date': self._parse_timestamp(data.get('listing_date'))
            }
        }
    
    def _normalize_polkastarter(self, data: Dict) -> Dict:
        """Normalize Polkastarter data format"""
        return {
            'platform': 'polkastarter',
            'id': data.get('id'),
            'name': data.get('name'),
            'symbol': data.get('ticker'),
            'description': data.get('description', ''),
            'start_time': self._parse_timestamp(data.get('start_date')),
            'end_time': self._parse_timestamp(data.get('end_date')),
            'hard_cap': float(data.get('hard_cap', 0)),
            'soft_cap': float(data.get('soft_cap', 0)),
            'token_price': float(data.get('token_price', 0)),
            'total_supply': float(data.get('total_tokens', 0)),
            'raised_amount': float(data.get('total_raised', 0)),
            'participants': int(data.get('participants', 0)),
            'website': data.get('website_url'),
            'whitepaper': data.get('whitepaper_url'),
            'social_links': {
                'twitter': data.get('twitter_url'),
                'telegram': data.get('telegram_url'),
                'discord': data.get('discord_url')
            },
            'audit_status': 'completed' if data.get('is_audited') else 'none',
            'kyc_status': data.get('is_kyc', False),
            'team_info': data.get('team_members', []),
            'tokenomics': data.get('token_distribution', {}),
            'vesting': data.get('vesting_schedule', {}),
            'listing_info': {
                'exchange': data.get('exchange_listing'),
                'date': self._parse_timestamp(data.get('exchange_listing_date'))
            }
        }
    
    def _normalize_seedify(self, data: Dict) -> Dict:
        """Normalize Seedify data format"""
        return {
            'platform': 'seedify',
            'id': data.get('_id'),
            'name': data.get('project_name'),
            'symbol': data.get('token_symbol'),
            'description': data.get('project_description', ''),
            'start_time': self._parse_timestamp(data.get('ido_start')),
            'end_time': self._parse_timestamp(data.get('ido_end')),
            'hard_cap': float(data.get('hard_cap_usd', 0)),
            'soft_cap': float(data.get('soft_cap_usd', 0)),
            'token_price': float(data.get('token_price_usd', 0)),
            'total_supply': float(data.get('total_supply', 0)),
            'raised_amount': float(data.get('amount_raised_usd', 0)),
            'participants': int(data.get('participant_count', 0)),
            'website': data.get('website'),
            'whitepaper': data.get('whitepaper_link'),
            'social_links': data.get('social_media', {}),
            'audit_status': data.get('audit_status'),
            'kyc_status': data.get('kyc_verified', False),
            'team_info': data.get('team', []),
            'tokenomics': data.get('tokenomics', {}),
            'vesting': data.get('vesting_info', {}),
            'listing_info': {
                'exchange': data.get('listing_exchange'),
                'date': self._parse_timestamp(data.get('listing_date'))
            }
        }
    
    def _normalize_generic(self, data: Dict, platform: str) -> Dict:
        """Generic normalization for unknown formats"""
        return {
            'platform': platform,
            'id': data.get('id') or data.get('_id'),
            'name': data.get('name') or data.get('project_name'),
            'symbol': data.get('symbol') or data.get('ticker'),
            'description': data.get('description', ''),
            'start_time': self._parse_timestamp(
                data.get('start_time') or data.get('start_date')
            ),
            'end_time': self._parse_timestamp(
                data.get('end_time') or data.get('end_date')
            ),
            'hard_cap': float(data.get('hard_cap', 0)),
            'soft_cap': float(data.get('soft_cap', 0)),
            'token_price': float(data.get('price', 0)),
            'total_supply': float(data.get('total_supply', 0)),
            'raised_amount': float(data.get('raised', 0)),
            'participants': int(data.get('participants', 0)),
            'website': data.get('website'),
            'whitepaper': data.get('whitepaper'),
            'social_links': data.get('social', {}),
            'audit_status': data.get('audit'),
            'kyc_status': data.get('kyc', False),
            'team_info': data.get('team', []),
            'tokenomics': data.get('tokenomics', {}),
            'vesting': data.get('vesting', {}),
            'listing_info': {}
        }
    
    def _parse_pinksale(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse PinkSale presales from HTML"""
        presales = []
        
        # Find presale cards
        cards = soup.find_all('div', class_='presale-card')
        
        for card in cards:
            try:
                presale = {
                    'platform': 'pinksale',
                    'id': card.get('data-id'),
                    'name': card.find('h3', class_='token-name').text.strip(),
                    'symbol': card.find('span', class_='token-symbol').text.strip(),
                    'description': '',
                    'hard_cap': self._extract_number(
                        card.find('div', class_='hard-cap').text
                    ),
                    'soft_cap': self._extract_number(
                        card.find('div', class_='soft-cap').text
                    ),
                    'raised_amount': self._extract_number(
                        card.find('div', class_='raised').text
                    ),
                    'status': card.find('span', class_='status').text.strip()
                }
                
                presales.append(presale)
                
            except Exception as e:
                logger.debug(f"Error parsing presale card: {e}")
                continue
        
        return presales
    
    def _parse_timestamp(self, timestamp) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if not timestamp:
            return None
        
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        
        if isinstance(timestamp, str):
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%d/%m/%Y %H:%M',
                '%d-%m-%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except:
                    continue
        
        return None
    
    def _extract_number(self, text: str) -> float:
        """Extract number from text"""
        if not text:
            return 0.0
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', text)
        
        try:
            return float(cleaned)
        except:
            return 0.0
    
    async def _analyze_presales(self, presales: List[Dict]) -> List[Dict]:
        """Analyze presales and identify opportunities"""
        opportunities = []
        
        for presale in presales:
            # Skip if already processed
            presale_id = f"{presale['platform']}_{presale['id']}"
            if presale_id in self.alerts_sent:
                continue
            
            # Analyze presale quality
            analysis = await self._analyze_presale_quality(presale)
            
            if analysis['score'] > 0.7:
                opportunity = {
                    'presale': presale,
                    'analysis': analysis,
                    'alert_time': datetime.now()
                }
                opportunities.append(opportunity)
                self.alerts_sent.add(presale_id)
        
        return opportunities
    
    async def _analyze_presale_quality(self, presale: Dict) -> Dict:
        """Analyze presale quality and potential"""
        scores = {
            'team_score': 0.5,
            'tokenomics_score': 0.5,
            'community_score': 0.5,
            'technical_score': 0.5,
            'timing_score': 0.5
        }
        
        # Team analysis
        if presale.get('kyc_status'):
            scores['team_score'] += 0.2
        if presale.get('team_info'):
            scores['team_score'] += 0.1
        
        # Tokenomics analysis
        if presale.get('vesting'):
            scores['tokenomics_score'] += 0.2
        
        hard_cap = presale.get('hard_cap', 0)
        if 100000 < hard_cap < 5000000:  # Reasonable cap
            scores['tokenomics_score'] += 0.2
        
        # Community analysis
        social_links = presale.get('social_links', {})
        if social_links.get('twitter') and social_links.get('telegram'):
            scores['community_score'] += 0.2
        
        if presale.get('participants', 0) > 100:
            scores['community_score'] += 0.2
        
        # Technical analysis
        if presale.get('audit_status') == 'completed':
            scores['technical_score'] += 0.3
        if presale.get('whitepaper'):
            scores['technical_score'] += 0.1
        
        # Timing analysis
        start_time = presale.get('start_time')
        if start_time and start_time > datetime.now():
            # Presale hasn't started yet - good for preparation
            scores['timing_score'] += 0.3
        
        # ML prediction if available
        ml_score = 0.5
        if self.ml_models:
            features = self._extract_ml_features(presale)
            ml_score = self.ml_models.predict_presale_success(features)
        
        # Calculate weighted total score
        total_score = (
            scores['team_score'] * 0.2 +
            scores['tokenomics_score'] * 0.2 +
            scores['community_score'] * 0.15 +
            scores['technical_score'] * 0.25 +
            scores['timing_score'] * 0.1 +
            ml_score * 0.1
        )
        
        return {
            'score': total_score,
            'scores': scores,
            'ml_score': ml_score,
            'red_flags': self._identify_red_flags(presale),
            'positive_factors': self._identify_positive_factors(presale)
        }
    
    def _extract_ml_features(self, presale: Dict) -> Dict:
        """Extract features for ML model"""
        return {
            'hard_cap': presale.get('hard_cap', 0),
            'soft_cap': presale.get('soft_cap', 0),
            'token_price': presale.get('token_price', 0),
            'total_supply': presale.get('total_supply', 0),
            'team_score': 0.8 if presale.get('kyc_status') else 0.3,
            'community_size': presale.get('participants', 0) * 10,  # Estimate
            'social_engagement': 0.7 if presale.get('social_links') else 0.3,
            'whitepaper_score': 0.8 if presale.get('whitepaper') else 0.2,
            'audit_score': 0.9 if presale.get('audit_status') == 'completed' else 0.2,
            'market_cap_at_launch': presale.get('hard_cap', 0) * 2,  # Estimate
            'vesting_period_days': 180 if presale.get('vesting') else 0,
            'team_allocation_pct': 20,  # Default estimate
            'liquidity_lock_days': 365 if presale.get('vesting') else 0,
            'marketing_budget_pct': 10,  # Default estimate
            'similar_projects_success_rate': 0.3  # Historical average
        }
    
    def _identify_red_flags(self, presale: Dict) -> List[str]:
        """Identify potential red flags"""
        red_flags = []
        
        if not presale.get('audit_status'):
            red_flags.append('No audit')
        
        if not presale.get('kyc_status'):
            red_flags.append('Team not KYC verified')
        
        if presale.get('hard_cap', 0) > 10000000:
            red_flags.append('Very high hard cap')
        
        if not presale.get('vesting'):
            red_flags.append('No vesting information')
        
        if not presale.get('whitepaper'):
            red_flags.append('No whitepaper')
        
        return red_flags
    
    def _identify_positive_factors(self, presale: Dict) -> List[str]:
        """Identify positive factors"""
        positives = []
        
        if presale.get('audit_status') == 'completed':
            positives.append('Audited')
        
        if presale.get('kyc_status'):
            positives.append('KYC verified team')
        
        if presale.get('raised_amount', 0) > presale.get('soft_cap', 0):
            positives.append('Soft cap reached')
        
        if len(presale.get('social_links', {})) >= 3:
            positives.append('Strong social presence')
        
        listing_info = presale.get('listing_info', {})
        if listing_info.get('exchange'):
            positives.append(f"Confirmed {listing_info['exchange']} listing")
        
        return positives
    
    async def _process_opportunity(self, opportunity: Dict):
        """Process identified presale opportunity"""
        presale = opportunity['presale']
        analysis = opportunity['analysis']
        
        # Store in active presales
        presale_id = f"{presale['platform']}_{presale['id']}"
        self.active_presales[presale_id] = {
            'presale': presale,
            'analysis': analysis,
            'discovered_at': datetime.now(),
            'status': 'monitoring'
        }
        
        logger.info(
            f"New presale opportunity: {presale['name']} ({presale['symbol']}) "
            f"on {presale['platform']} - Score: {analysis['score']:.2f}"
        )
    
    def get_active_opportunities(self) -> List[Dict]:
        """Get current presale opportunities"""
        opportunities = []
        
        for presale_id, data in self.active_presales.items():
            presale = data['presale']
            analysis = data['analysis']
            
            # Calculate time until start
            start_time = presale.get('start_time')
            time_until_start = None
            if start_time and start_time > datetime.now():
                time_until_start = (start_time - datetime.now()).total_seconds() / 3600
            
            opportunities.append({
                'id': presale_id,
                'name': presale['name'],
                'symbol': presale['symbol'],
                'platform': presale['platform'],
                'score': analysis['score'],
                'hard_cap': presale.get('hard_cap', 0),
                'token_price': presale.get('token_price', 0),
                'start_time': start_time,
                'time_until_start_hours': time_until_start,
                'raised_pct': (presale.get('raised_amount', 0) / 
                              presale.get('hard_cap', 1)) * 100,
                'red_flags': analysis['red_flags'],
                'positive_factors': analysis['positive_factors'],
                'status': data['status']
            })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities
    
    async def close(self):
        """Close monitor connections"""
        if self.session:
            await self.session.close()
