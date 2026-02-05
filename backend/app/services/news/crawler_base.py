"""高级爬虫基础架构 - 包含重试、代理、速率限制等功能"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import aiohttp
from fake_useragent import UserAgent
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """爬虫配置"""
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
    retry_backoff: float = 2.0  # 指数退避因子

    # 速率限制
    requests_per_second: float = 2.0
    burst_size: int = 5

    # 超时配置
    connect_timeout: float = 10.0
    read_timeout: float = 30.0

    # 代理配置
    proxy_url: Optional[str] = None
    proxy_rotation: bool = False
    proxy_list: List[str] = field(default_factory=list)

    # User-Agent轮换
    rotate_user_agent: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒


class RateLimiter:
    """令牌桶算法实现的速率限制器"""

    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: 每秒允许的请求数
            burst: 突发请求数量
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取令牌，如果没有令牌则等待"""
        async with self._lock:
            now = time.time()
            # 补充令牌
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            # 如果没有令牌，等待
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ProxyManager:
    """代理管理器"""

    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.current_index = 0
        self.failed_proxies = set()
        self._lock = asyncio.Lock()

    async def get_proxy(self) -> Optional[str]:
        """获取可用的代理"""
        if not self.proxy_list:
            return None

        async with self._lock:
            available_proxies = [
                p for p in self.proxy_list
                if p not in self.failed_proxies
            ]

            if not available_proxies:
                # 重置失败代理列表
                logger.warning("All proxies failed, resetting...")
                self.failed_proxies.clear()
                available_proxies = self.proxy_list

            # 轮询选择代理
            proxy = available_proxies[self.current_index % len(available_proxies)]
            self.current_index += 1
            return proxy

    async def mark_proxy_failed(self, proxy: str):
        """标记代理失败"""
        async with self._lock:
            self.failed_proxies.add(proxy)
            logger.warning(f"Proxy {proxy} marked as failed")


class CrawlerSession:
    """爬虫会话管理器"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            config.requests_per_second,
            config.burst_size
        )
        self.proxy_manager = ProxyManager(config.proxy_list) if config.proxy_list else None
        self.user_agent = UserAgent() if config.rotate_user_agent else None
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, tuple[Any, float]] = {}  # {url: (data, timestamp)}

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(
            connect=self.config.connect_timeout,
            total=self.config.read_timeout
        )
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        headers = self.config.custom_headers.copy()

        if self.user_agent and self.config.rotate_user_agent:
            headers["User-Agent"] = self.user_agent.random
        elif "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

        return headers

    def _is_cache_valid(self, url: str) -> bool:
        """检查缓存是否有效"""
        if not self.config.enable_cache or url not in self._cache:
            return False

        _, timestamp = self._cache[url]
        return time.time() - timestamp < self.config.cache_ttl

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        执行HTTP请求（带重试、代理、速率限制）

        Args:
            url: 请求URL
            method: HTTP方法
            **kwargs: 其他请求参数

        Returns:
            响应对象
        """
        # 检查缓存
        if method == "GET" and self._is_cache_valid(url):
            logger.debug(f"Cache hit for {url}")
            cached_data, _ = self._cache[url]
            return cached_data

        # 速率限制
        await self.rate_limiter.acquire()

        retry_count = 0
        last_exception = None

        while retry_count <= self.config.max_retries:
            try:
                # 获取代理
                proxy = None
                if self.proxy_manager:
                    proxy = await self.proxy_manager.get_proxy()

                # 准备请求参数
                headers = self._get_headers()
                request_kwargs = {
                    "headers": headers,
                    "proxy": proxy,
                    **kwargs
                }

                # 执行请求
                logger.debug(f"Fetching {url} (attempt {retry_count + 1}/{self.config.max_retries + 1})")
                async with self.session.request(method, url, **request_kwargs) as response:
                    response.raise_for_status()

                    # 缓存成功的GET请求
                    if method == "GET" and self.config.enable_cache:
                        self._cache[url] = (response, time.time())

                    return response

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                retry_count += 1

                # 标记代理失败
                if proxy and self.proxy_manager:
                    await self.proxy_manager.mark_proxy_failed(proxy)

                if retry_count <= self.config.max_retries:
                    # 指数退避
                    delay = self.config.retry_delay * (self.config.retry_backoff ** (retry_count - 1))
                    logger.warning(
                        f"Request to {url} failed: {e}. "
                        f"Retrying in {delay:.2f}s (attempt {retry_count}/{self.config.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request to {url} failed after {retry_count} attempts: {e}")
                    raise

        raise last_exception

    async def fetch_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """获取JSON数据"""
        response = await self.fetch(url, **kwargs)
        return await response.json()

    async def fetch_text(self, url: str, **kwargs) -> str:
        """获取文本数据"""
        response = await self.fetch(url, **kwargs)
        return await response.text()


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_items": 0,
            "start_time": None,
            "end_time": None,
        }

    @abstractmethod
    async def crawl(self, **kwargs) -> List[Any]:
        """执行爬虫任务"""
        pass

    async def run(self, **kwargs) -> List[Any]:
        """运行爬虫（带统计）"""
        self.stats["start_time"] = datetime.now()

        try:
            async with CrawlerSession(self.config) as session:
                self.session = session
                results = await self.crawl(**kwargs)
                self.stats["total_items"] = len(results)
                return results
        finally:
            self.stats["end_time"] = datetime.now()
            self._log_stats()

    def _log_stats(self):
        """记录统计信息"""
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            success_rate = (
                self.stats["successful_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            )

            logger.info(
                f"Crawler statistics:\n"
                f"  Duration: {duration:.2f}s\n"
                f"  Total requests: {self.stats['total_requests']}\n"
                f"  Successful: {self.stats['successful_requests']} ({success_rate:.1f}%)\n"
                f"  Failed: {self.stats['failed_requests']}\n"
                f"  Items collected: {self.stats['total_items']}\n"
                f"  Items/second: {self.stats['total_items'] / duration:.2f}"
            )


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """装饰器：异常时重试"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count <= max_retries:
                        wait_time = delay * (backoff ** (retry_count - 1))
                        logger.warning(
                            f"{func.__name__} failed: {e}. "
                            f"Retrying in {wait_time:.2f}s (attempt {retry_count}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator
