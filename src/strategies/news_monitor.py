import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
import feedparser
from textblob import TextBlob
import praw
import tweepy

logger = logging.getLogger(__name__)

class NewsMonitor:
    """Monitor news sources and social media for crypto opportunities"""
    
    def __init__(self, credentials: Dict = None, ml_models=None):
        self.credentials = credentials or {}
        self.ml_models = ml_models
        self.session = None
        
        # Initialize API clients
        self._init_api_clients()
        
        # News sources
        self.news_sources = {
            'cryptonews': {
                'rss': 'https://cryptonews.com/news/feed/',
                'type': 'rss',
                'weight': 0.8
            },
            'coindesk': {
                'rss': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'type': 'rss',
                'weight': 0.9
            },
            'cointelegraph': {
                'rss': 'https://cointelegraph.com/rss',
                'type': 'rss',
                'weight': 0.9
            },
            'cryptoslate': {
                'rss': 'https://cryptoslate.com/feed/',
                'type': 'rss',
                'weight': 0.7
            },
            'bitcoinmagazine': {
                'rss': 'https://bitcoinmagazine.com/feed',
                'type': 'rss',
                'weight': 0.8
            },
            'decrypt': {
                'url': 'https://decrypt.co/news',
                'type': 'scrape',
                'weight': 0.7
            }
        }
        
        # Social media monitoring
        self.social_sources = {
            'twitter_accounts': [
                '@CryptoWhale', '@APompliano', '@WuBlockchain', 
                '@CryptoGuru', '@TheCryptoLark', '@IvanOnTech',
                '@CryptoCobain', '@CryptoKaleo', '@PeterLBrandt'
            ],
            'reddit_subs': [
                'CryptoCurrency', 'CryptoMoonShots', 'SatoshiStreetBets',
                'altcoin', 'CryptoMarkets', 'ICOAnalysis'
            ],
            'telegram_channels': [
                'crypto_signals_binance', 'whale_alert_io',
                'crypto_news_flash', 'insider_crypto_trading'
            ],
            'discord_tracking': [
                'major_crypto_servers', 'defi_alpha', 'nft_flippers'
            ]
        }
        
        # Track news and sentiment
        self.news_cache = []
        self.sentiment_history = {}
        self.trending_tokens = {}
        self.source_performance = {}
        
        # ML features
        self.token_mentions = {}  # Track mention frequency
        self.sentiment_scores = {}  # Track sentiment over time
        
    def _init_api_clients(self):
        """Initialize API clients for social media"""
        # Twitter API
        if self.credentials.get('twitter'):
            self.twitter = tweepy.Client(
                bearer_token=self.credentials['twitter']['bearer_token']
            )
        else:
            self.twitter = None
        
        # Reddit API
        if self.credentials.get('reddit'):
            self.reddit = praw.Reddit(
                client_id=self.credentials['reddit']['client_id'],
                client_secret=self.credentials['reddit']['client_secret'],
                user_agent='crypto-monitor'
            )
        else:
            self.reddit = None
    
    async def start_monitoring(self):
        """Start monitoring news and social media"""
        self.session = aiohttp.ClientSession()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_news()),
            asyncio.create_task(self._monitor_twitter()),
            asyncio.create_task(self._monitor_reddit()),
            asyncio.create_task(self._analyze_trends()),
            asyncio.create_task(self._track_source_performance())
        ]
        
        await asyncio.gather(*tasks)
    
    async def _monitor_news(self):
        """Monitor news sources"""
        while True:
            try:
                all_articles = []
                
                # Fetch from each source
                for source_name, config in self.news_sources.items():
                    if config['type'] == 'rss':
                        articles = await self._fetch_rss_feed(
                            source_name, config['rss']
                        )
                    else:
                        articles = await self._scrape_news_site(
                            source_name, config['url']
                        )
                    
                    # Add source weight
                    for article in articles:
                        article['source_weight'] = config['weight']
                    
                    all_articles.extend(articles)
                
                # Analyze articles
                new_opportunities = await self._analyze_news_articles(all_articles)
                
                # Process opportunities
                for opportunity in new_opportunities:
                    await self._process_news_opportunity(opportunity)
                
                await asyncio.sleep(900)  # 15 minutes
                
            except Exception as e:
                logger.error(f"News monitoring error: {e}")
                await asyncio.sleep(900)
    
    async def _fetch_rss_feed(self, source: str, url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        articles = []
        
        try:
            # Use feedparser for RSS
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:20]:  # Last 20 articles
                # Extract relevant info
                article = {
                    'source': source,
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published': self._parse_rss_date(entry.get('published')),
                    'summary': entry.get('summary', ''),
                    'content': self._extract_content(entry),
                    'id': entry.get('id', entry.get('link', ''))
                }
                
                articles.append(article)
                
        except Exception as e:
            logger.error(f"RSS fetch error for {source}: {e}")
        
        return articles
    
    async def _scrape_news_site(self, source: str, url: str) -> List[Dict]:
        """Scrape news website"""
        articles = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract articles based on common patterns
                    article_elements = soup.find_all(['article', 'div'], 
                                                   class_=re.compile('article|post|news-item'))
                    
                    for elem in article_elements[:20]:
                        article = self._extract_article_from_element(elem, source)
                        if article:
                            articles.append(article)
                            
        except Exception as e:
            logger.error(f"Scraping error for {source}: {e}")
        
        return articles
    
    def _extract_article_from_element(self, elem, source: str) -> Optional[Dict]:
        """Extract article data from HTML element"""
        try:
            # Find title
            title_elem = elem.find(['h1', 'h2', 'h3', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            
            # Find link
            link_elem = elem.find('a')
            url = link_elem['href'] if link_elem else ''
            
            # Find content/summary
            content_elem = elem.find(['p', 'div'], class_=re.compile('summary|excerpt|content'))
            content = content_elem.text.strip() if content_elem else ''
            
            return {
                'source': source,
                'title': title,
                'url': url,
                'published': datetime.now(),
                'summary': content[:200],
                'content': content,
                'id': url or title
            }
            
        except Exception as e:
            logger.debug(f"Article extraction error: {e}")
            return None
    
    async def _monitor_twitter(self):
        """Monitor Twitter for crypto signals"""
        if not self.twitter:
            logger.warning("Twitter API not configured")
            return
        
        while True:
            try:
                tweets = []
                
                # Search for trending crypto topics
                trending_queries = [
                    'new crypto listing',
                    'token launch',
                    'IDO announcement',
                    'airdrop confirmed',
                    'listing confirmed'
                ]
                
                for query in trending_queries:
                    try:
                        # Search recent tweets
                        response = self.twitter.search_recent_tweets(
                            query=f"{query} -is:retweet",
                            max_results=50,
                            tweet_fields=['created_at', 'author_id', 'public_metrics']
                        )
                        
                        if response.data:
                            tweets.extend(response.data)
                    except Exception as e:
                        logger.error(f"Twitter search error: {e}")
                
                # Monitor specific accounts
                for account in self.social_sources['twitter_accounts']:
                    try:
                        # Get user tweets
                        user = self.twitter.get_user(username=account.lstrip('@'))
                        if user.data:
                            timeline = self.twitter.get_users_tweets(
                                user.data.id,
                                max_results=10,
                                tweet_fields=['created_at', 'public_metrics']
                            )
                            
                            if timeline.data:
                                tweets.extend(timeline.data)
                    except Exception as e:
                        logger.error(f"Twitter timeline error for {account}: {e}")
                
                # Analyze tweets
                signals = await self._analyze_twitter_signals(tweets)
                
                for signal in signals:
                    await self._process_social_signal(signal, 'twitter')
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Twitter monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_reddit(self):
        """Monitor Reddit for crypto opportunities"""
        if not self.reddit:
            logger.warning("Reddit API not configured")
            return
        
        while True:
            try:
                posts = []
                
                # Monitor each subreddit
                for sub_name in self.social_sources['reddit_subs']:
                    try:
                        subreddit = self.reddit.subreddit(sub_name)
                        
                        # Get hot and new posts
                        hot_posts = list(subreddit.hot(limit=20))
                        new_posts = list(subreddit.new(limit=20))
                        
                        posts.extend(hot_posts + new_posts)
                        
                    except Exception as e:
                        logger.error(f"Reddit sub error for {sub_name}: {e}")
                
                # Analyze posts
                signals = await self._analyze_reddit_signals(posts)
                
                for signal in signals:
                    await self._process_social_signal(signal, 'reddit')
                
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Reddit monitoring error: {e}")
                await asyncio.sleep(600)
    
    async def _analyze_news_articles(self, articles: List[Dict]) -> List[Dict]:
        """Analyze news articles for opportunities"""
        opportunities = []
        
        # Check against cache to find new articles
        cached_ids = {item['id'] for item in self.news_cache[-1000:]}
        
        for article in articles:
            if article['id'] in cached_ids:
                continue
            
            # Analyze article
            analysis = await self._analyze_article_content(article)
            
            if analysis['opportunity_score'] > 0.7:
                opportunities.append({
                    'article': article,
                    'analysis': analysis,
                    'timestamp': datetime.now()
                })
            
            # Update cache
            self.news_cache.append(article)
        
        # Trim cache
        self.news_cache = self.news_cache[-2000:]
        
        return opportunities
    
    async def _analyze_article_content(self, article: Dict) -> Dict:
        """Analyze article for crypto opportunities"""
        text = f"{article['title']} {article['summary']} {article['content']}"
        
        # Extract mentioned tokens
        tokens = self._extract_token_mentions(text)
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(text)
        
        # Opportunity keywords
        opportunity_score = self._calculate_opportunity_score(text)
        
        # ML prediction if available
        ml_score = 0.5
        if self.ml_models and tokens:
            features = {
                'sentiment': sentiment,
                'source_weight': article.get('source_weight', 0.5),
                'mention_count': len(tokens),
                'opportunity_keywords': opportunity_score
            }
            ml_score = self.ml_models.predict_news_impact(features)
        
        # Weighted final score
        final_score = (
            opportunity_score * 0.4 +
            article.get('source_weight', 0.5) * 0.2 +
            (sentiment + 1) / 2 * 0.2 +  # Normalize to 0-1
            ml_score * 0.2
        )
        
        return {
            'opportunity_score': final_score,
            'tokens': tokens,
            'sentiment': sentiment,
            'ml_score': ml_score,
            'key_phrases': self._extract_key_phrases(text)
        }
    
    def _extract_token_mentions(self, text: str) -> List[str]:
        """Extract cryptocurrency token mentions"""
        tokens = []
        
        # Pattern for token symbols
        token_pattern = r'\b([A-Z]{2,10})\b'
        
        # Common crypto-related context words
        context_words = [
            'token', 'coin', 'crypto', 'listing', 'launch',
            'airdrop', 'IDO', 'ICO', 'presale', 'trade'
        ]
        
        # Find potential tokens
        words = text.split()
        
        for i, word in enumerate(words):
            match = re.match(token_pattern, word)
            if match:
                symbol = match.group(1)
                
                # Check context
                context_range = 5
                start = max(0, i - context_range)
                end = min(len(words), i + context_range + 1)
                
                context = ' '.join(words[start:end]).lower()
                
                if any(ctx in context for ctx in context_words):
                    if symbol not in ['THE', 'NEW', 'USD', 'EUR', 'API']:
                        tokens.append(symbol)
        
        return list(set(tokens))
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze text sentiment"""
        try:
            blob = TextBlob(text)
            
            # Get polarity (-1 to 1)
            sentiment = blob.sentiment.polarity
            
            # Boost for positive crypto keywords
            positive_keywords = [
                'bullish', 'moon', 'pump', 'breakout', 'surge',
                'rally', 'boom', 'explode', 'skyrocket'
            ]
            
            negative_keywords = [
                'bearish', 'dump', 'crash', 'scam', 'rug',
                'hack', 'exploit', 'warning', 'avoid'
            ]
            
            text_lower = text.lower()
            
            for keyword in positive_keywords:
                if keyword in text_lower:
                    sentiment += 0.1
            
            for keyword in negative_keywords:
                if keyword in text_lower:
                    sentiment -= 0.1
            
            # Clamp to [-1, 1]
            return max(-1, min(1, sentiment))
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return 0.0
    
    def _calculate_opportunity_score(self, text: str) -> float:
        """Calculate opportunity score based on keywords"""
        text_lower = text.lower()
        
        score = 0.5
        
        # High value keywords
        high_value = [
            'listing confirmed', 'will list', 'listing announcement',
            'launches on', 'trading starts', 'goes live',
            'presale ending', 'IDO tomorrow', 'airdrop confirmed'
        ]
        
        # Medium value keywords
        medium_value = [
            'partnership', 'integration', 'mainnet launch',
            'major update', 'new feature', 'staking enabled'
        ]
        
        # Check keywords
        for keyword in high_value:
            if keyword in text_lower:
                score += 0.2
        
        for keyword in medium_value:
            if keyword in text_lower:
                score += 0.1
        
        return min(1.0, score)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        key_phrases = []
        
        # Patterns for important phrases
        patterns = [
            r'listing on ([A-Za-z]+)',
            r'launches ([A-Za-z]+ \d+)',
            r'available on ([A-Za-z]+)',
            r'([A-Z]{2,10}) (?:token|coin) (?:listing|launch)',
            r'presale (?:starts|ends) ([A-Za-z]+ \d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_phrases.extend(matches)
        
        return key_phrases[:5]  # Top 5 phrases
    
    async def _analyze_twitter_signals(self, tweets) -> List[Dict]:
        """Analyze tweets for trading signals"""
        signals = []
        
        for tweet in tweets:
            try:
                text = tweet.text
                metrics = tweet.public_metrics
                
                # Skip low engagement tweets
                if metrics['like_count'] < 10:
                    continue
                
                # Analyze content
                tokens = self._extract_token_mentions(text)
                sentiment = self._analyze_sentiment(text)
                
                # Calculate signal strength
                engagement_score = (
                    metrics['like_count'] * 0.3 +
                    metrics['retweet_count'] * 0.5 +
                    metrics['reply_count'] * 0.2
                ) / 100  # Normalize
                
                if tokens and (sentiment > 0.3 or 'listing' in text.lower()):
                    signals.append({
                        'source': 'twitter',
                        'author': tweet.author_id,
                        'text': text,
                        'tokens': tokens,
                        'sentiment': sentiment,
                        'engagement': engagement_score,
                        'timestamp': tweet.created_at
                    })
                    
            except Exception as e:
                logger.debug(f"Tweet analysis error: {e}")
        
        return signals
    
    async def _analyze_reddit_signals(self, posts) -> List[Dict]:
        """Analyze Reddit posts for signals"""
        signals = []
        
        for post in posts:
            try:
                # Combine title and body
                text = f"{post.title} {post.selftext}"
                
                # Skip low quality posts
                if post.score < 5:
                    continue
                
                # Analyze content
                tokens = self._extract_token_mentions(text)
                sentiment = self._analyze_sentiment(text)
                
                # Calculate signal strength
                engagement_score = (
                    post.score * 0.4 +
                    post.num_comments * 0.3 +
                    post.upvote_ratio * 0.3
                ) / 100
                
                if tokens:
                    signals.append({
                        'source': 'reddit',
                        'subreddit': post.subreddit.display_name,
                        'author': str(post.author),
                        'text': text[:500],
                        'tokens': tokens,
                        'sentiment': sentiment,
                        'engagement': engagement_score,
                        'timestamp': datetime.fromtimestamp(post.created_utc),
                        'url': f"https://reddit.com{post.permalink}"
                    })
                    
            except Exception as e:
                logger.debug(f"Reddit analysis error: {e}")
        
        return signals
    
    async def _analyze_trends(self):
        """Analyze trending tokens across sources"""
        while True:
            try:
                # Aggregate mentions from last hour
                cutoff = datetime.now() - timedelta(hours=1)
                
                recent_mentions = {}
                
                # Count mentions across all sources
                for source_type in ['news', 'twitter', 'reddit']:
                    mentions = self._get_recent_mentions(source_type, cutoff)
                    
                    for token, count in mentions.items():
                        if token not in recent_mentions:
                            recent_mentions[token] = {
                                'total': 0,
                                'sources': {},
                                'sentiment_sum': 0,
                                'sentiment_count': 0
                            }
                        
                        recent_mentions[token]['total'] += count
                        recent_mentions[token]['sources'][source_type] = count
                
                # Identify trending tokens
                for token, data in recent_mentions.items():
                    if data['total'] > 5:  # Minimum threshold
                        trend_score = self._calculate_trend_score(token, data)
                        
                        if trend_score > 0.7:
                            self.trending_tokens[token] = {
                                'score': trend_score,
                                'mentions': data,
                                'timestamp': datetime.now()
                            }
                
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")
                await asyncio.sleep(3600)
    
    def _get_recent_mentions(self, source_type: str, cutoff: datetime) -> Dict[str, int]:
        """Get recent token mentions by source"""
        mentions = {}
        
        # This would query stored mentions from database
        # For now, return empty dict
        return mentions
    
    def _calculate_trend_score(self, token: str, data: Dict) -> float:
        """Calculate trending score for token"""
        # Base score on mention count
        mention_score = min(data['total'] / 50, 1.0)
        
        # Source diversity bonus
        source_diversity = len(data['sources']) / 3
        
        # Historical comparison
        historical_avg = self.token_mentions.get(token, {}).get('daily_avg', 5)
        growth_rate = data['total'] / max(historical_avg, 1)
        growth_score = min(growth_rate / 5, 1.0)
        
        # Sentiment factor
        avg_sentiment = (
            data['sentiment_sum'] / max(data['sentiment_count'], 1)
            if data['sentiment_count'] > 0 else 0
        )
        sentiment_score = (avg_sentiment + 1) / 2  # Normalize to 0-1
        
        # Weighted score
        trend_score = (
            mention_score * 0.3 +
            source_diversity * 0.2 +
            growth_score * 0.3 +
            sentiment_score * 0.2
        )
        
        return trend_score
    
    async def _track_source_performance(self):
        """Track performance of different news sources"""
        while True:
            try:
                # Analyze which sources provide early/accurate signals
                for source in self.news_sources:
                    performance = await self._analyze_source_performance(source)
                    self.source_performance[source] = performance
                
                # Log top performing sources
                top_sources = sorted(
                    self.source_performance.items(),
                    key=lambda x: x[1].get('score', 0),
                    reverse=True
                )[:5]
                
                logger.info(f"Top news sources: {[s[0] for s in top_sources]}")
                
                await asyncio.sleep(86400)  # Daily
                
            except Exception as e:
                logger.error(f"Source tracking error: {e}")
                await asyncio.sleep(86400)
    
    async def _analyze_source_performance(self, source: str) -> Dict:
        """Analyze historical performance of news source"""
        # This would analyze historical data
        # For now, return placeholder
        return {
            'accuracy': 0.5,
            'timeliness': 0.5,
            'signal_quality': 0.5,
            'score': 0.5
        }
    
    async def _process_news_opportunity(self, opportunity: Dict):
        """Process identified news opportunity"""
        article = opportunity['article']
        analysis = opportunity['analysis']
        
        logger.info(
            f"News opportunity from {article['source']}: "
            f"{article['title']} - Score: {analysis['opportunity_score']:.2f}"
        )
        
        # Update token tracking
        for token in analysis['tokens']:
            if token not in self.token_mentions:
                self.token_mentions[token] = {
                    'first_seen': datetime.now(),
                    'mentions': []
                }
            
            self.token_mentions[token]['mentions'].append({
                'source': article['source'],
                'timestamp': datetime.now(),
                'sentiment': analysis['sentiment'],
                'url': article['url']
            })
    
    async def _process_social_signal(self, signal: Dict, platform: str):
        """Process social media signal"""
        logger.info(
            f"Social signal from {platform}: "
            f"Tokens: {signal['tokens']} - "
            f"Engagement: {signal['engagement']:.2f}"
        )
    
    def _parse_rss_date(self, date_str: str) -> datetime:
        """Parse RSS date string"""
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return datetime.now()
    
    def _extract_content(self, entry) -> str:
        """Extract content from RSS entry"""
        # Try different content fields
        content = entry.get('content', [])
        if content and isinstance(content, list):
            return content[0].get('value', '')
        
        return entry.get('description', '')
    
    def get_trending_tokens(self) -> List[Dict]:
        """Get currently trending tokens"""
        trending = []
        
        for token, data in self.trending_tokens.items():
            trending.append({
                'symbol': token,
                'trend_score': data['score'],
                'total_mentions': data['mentions']['total'],
                'sources': data['mentions']['sources'],
                'last_updated': data['timestamp']
            })
        
        # Sort by trend score
        trending.sort(key=lambda x: x['trend_score'], reverse=True)
        
        return trending[:20]  # Top 20
    
    def get_source_performance(self) -> Dict:
        """Get performance metrics for all sources"""
        return {
            'news_sources': self.source_performance,
            'most_accurate': self._get_top_sources('accuracy'),
            'most_timely': self._get_top_sources('timeliness'),
            'best_overall': self._get_top_sources('score')
        }
    
    def _get_top_sources(self, metric: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top sources by specific metric"""
        sources = [
            (source, perf.get(metric, 0))
            for source, perf in self.source_performance.items()
        ]
        
        sources.sort(key=lambda x: x[1], reverse=True)
        
        return sources[:limit]
    
    async def close(self):
        """Close monitor connections"""
        if self.session:
            await self.session.close()
