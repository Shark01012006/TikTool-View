import aiohttp
import asyncio
import random
import requests
import re
import time
import secrets
import os
import signal
import sys
from hashlib import md5
from time import time as T
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    model: str
    version: str
    api_level: int

class DeviceGenerator:
    
    DEVICES = [
        DeviceInfo("Pixel 6", "12", 31),
        DeviceInfo("Pixel 5", "11", 30),
        DeviceInfo("Samsung Galaxy S21", "13", 33),
        DeviceInfo("Oppo Reno 8", "12", 31),
        DeviceInfo("Xiaomi Mi 11", "12", 31),
        DeviceInfo("OnePlus 9", "13", 33),
        DeviceInfo("Huawei P50", "12", 31),
        DeviceInfo("Vivo X80", "13", 33),
        DeviceInfo("Realme GT", "12", 31),
        DeviceInfo("Nokia X20", "11", 30),
        DeviceInfo("Sony Xperia 5", "13", 33),
        DeviceInfo("LG Velvet", "12", 31),
        DeviceInfo("Asus Zenfone 8", "11", 30),
        DeviceInfo("Motorola Edge 20", "12", 31),
        DeviceInfo("ZTE Axon 30", "11", 30),
    ]
    
    @classmethod
    def random_device(cls) -> DeviceInfo:
        return random.choice(cls.DEVICES)

class Signature:
    
    
    KEY = [0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83, 0xD1, 0xB9, 
           0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85, 0xC3, 0xD0, 0xFB, 0xC3]
    
    def __init__(self, params: str, data: str, cookies: str):
        self.params = params
        self.data = data
        self.cookies = cookies
    
    def _md5_hash(self, data: str) -> str:
        return md5(data.encode()).hexdigest()
    
    def _reverse_byte(self, n: int) -> int:
        return int(f"{n:02x}"[1:] + f"{n:02x}"[0], 16)
    
    def generate(self) -> Dict[str, str]:
        
        g = self._md5_hash(self.params)
        g += self._md5_hash(self.data) if self.data else "0" * 32
        g += self._md5_hash(self.cookies) if self.cookies else "0" * 32
        g += "0" * 32
        
        unix_timestamp = int(T())
        payload = []
        
        for i in range(0, 12, 4):
            chunk = g[8 * i:8 * (i + 1)]
            for j in range(4):
                payload.append(int(chunk[j * 2:(j + 1) * 2], 16))
        
        payload.extend([0x0, 0x6, 0xB, 0x1C])
        payload.extend([
            (unix_timestamp & 0xFF000000) >> 24,
            (unix_timestamp & 0x00FF0000) >> 16,
            (unix_timestamp & 0x0000FF00) >> 8,
            (unix_timestamp & 0x000000FF)
        ])
        
        encrypted = [a ^ b for a, b in zip(payload, self.KEY)]
        
        for i in range(0x14):
            C = self._reverse_byte(encrypted[i])
            D = encrypted[(i + 1) % 0x14]
            F = int(bin(C ^ D)[2:].zfill(8)[::-1], 2)
            H = ((F ^ 0xFFFFFFFF) ^ 0x14) & 0xFF
            encrypted[i] = H
        
        signature = "".join(f"{x:02x}" for x in encrypted)
        
        return {
            "X-Gorgon": "840280416000" + signature,
            "X-Khronos": str(unix_timestamp)
        }

class PerformanceOptimizer:
    
    
    @staticmethod
    def calculate_optimal_workers() -> int:
        
        cpu_count = os.cpu_count() or 1
        optimal_workers = min(100000, cpu_count * 2000)  
        return optimal_workers
    
    @staticmethod
    def adaptive_delay(current_requests: int, max_requests: int) -> float:
        
        base_delay = 0.001
        if current_requests > max_requests * 0.8:
            return base_delay * 10
        elif current_requests > max_requests * 0.5:
            return base_delay * 5
        return base_delay

class TikTokViewBot:
    
    
    def __init__(self):
        self.count = 0
        self.start_time = 0
        self.is_running = False
        self.session = None
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def init_session(self):
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=0,  # No limit on total connections
            limit_per_host=0,  # No limit per host
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'com.ss.android.ugc.trill/400304'},
            cookie_jar=aiohttp.DummyCookieJar()
        )
    
    async def close_session(self):
       
        if self.session:
            await self.session.close()
    
    def get_video_id(self, url: str) -> Optional[str]:
        
        try:
            response = requests.get(
                url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }, 
                timeout=15
            )
            response.raise_for_status()
            
            patterns = [
                r'"video":\{"id":"(\d+)"',
                r'"id":"(\d+)"',
                r'video/(\d+)',
                r'(\d{19})',
                r'"aweme_id":"(\d+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    video_id = match.group(1)
                    logger.info(f"✅ Found Video ID: {video_id}")
                    return video_id
            
            logger.error("❌ No video ID found in page")
            return None
                
        except Exception as e:
            logger.error(f"❌ Error getting video ID: {e}")
            return None
    
    def generate_request_data(self, video_id: str) -> Tuple[str, Dict, Dict, Dict]:
        
        device = DeviceGenerator.random_device()
        
        params = (
            f"channel=googleplay&aid=1233&app_name=musical_ly&version_code=400304"
            f"&device_platform=android&device_type={device.model.replace(' ', '+')}"
            f"&os_version={device.version}&device_id={random.randint(600000000000000, 699999999999999)}"
            f"&os_api={device.api_level}&app_language=vi&tz_name=Asia%2FHo_Chi_Minh"
        )
        
        url = f"https://api16-core-c-alisg.tiktokv.com/aweme/v1/aweme/stats/?{params}"
        
        data = {
            "item_id": video_id,
            "play_delta": 1,
            "action_time": int(time.time())
        }
        
        cookies = {"sessionid": secrets.token_hex(16)}
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "com.ss.android.ugc.trill/400304",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }
        
        return url, data, cookies, headers
    
    async def send_view_request(self, video_id: str, semaphore: asyncio.Semaphore) -> bool:
        """Gửi request view async với semaphore"""
        async with semaphore:
            try:
                url, data, cookies, base_headers = self.generate_request_data(video_id)
                
                
                sig = Signature(url.split('?')[1], str(data), str(cookies)).generate()
                headers = {**base_headers, **sig}
                
                async with self.session.post(
                    url, 
                    data=data, 
                    headers=headers, 
                    cookies=cookies,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        self.count += 1
                        self.successful_requests += 1
                        return True
                    else:
                        self.failed_requests += 1
                        return False
                        
            except Exception as e:
                self.failed_requests += 1
                return False
    
    async def view_sender(self, video_id: str, task_id: int, semaphore: asyncio.Semaphore):
        """Worker gửi view liên tục"""
        while self.is_running:
            await self.send_view_request(video_id, semaphore)
            
            
            current_speed = self.calculate_stats()["views_per_second"]
            if current_speed > 1000:  
                delay = random.uniform(0.01, 0.05)
            else:
                delay = random.uniform(0.001, 0.01)
                
            await asyncio.sleep(delay)
    
    def calculate_stats(self) -> Dict[str, float]:
        
        elapsed = time.time() - self.start_time
        views_per_second = self.count / elapsed if elapsed > 0 else 0
        views_per_minute = views_per_second * 60
        views_per_hour = views_per_minute * 60
        
        success_rate = (self.successful_requests / (self.successful_requests + self.failed_requests)) * 100 if (self.successful_requests + self.failed_requests) > 0 else 0
        
        return {
            "total_views": self.count,
            "elapsed_time": elapsed,
            "views_per_second": views_per_second,
            "views_per_minute": views_per_minute,
            "views_per_hour": views_per_hour,
            "success_rate": success_rate,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests
        }
    
    def display_stats(self):
        
        stats = self.calculate_stats()
        print(f"\n{'='*60}")
        print(f"📊 THỐNG KÊ HIỆU SUẤT - 100,000 TASKS")
        print(f"{'='*60}")
        print(f"👀 Tổng view: {stats['total_views']:,}")
        print(f"⏰ Thời gian: {stats['elapsed_time']:.1f}s")
        print(f"🚀 Tốc độ: {stats['views_per_second']:.1f} view/s")
        print(f"📈 Dự kiến: {stats['views_per_minute']:,.0f} view/phút")
        print(f"🏃‍♂️ Dự kiến: {stats['views_per_hour']:,.0f} view/giờ")
        print(f"✅ Request thành công: {stats['successful_requests']:,}")
        print(f"❌ Request thất bại: {stats['failed_requests']:,}")
        print(f"🎯 Tỷ lệ thành công: {stats['success_rate']:.1f}%")
        print(f"{'='*60}")
    
    async def run(self, video_url: str):
        
        print("🔄 Đang lấy Video ID...")
        video_id = self.get_video_id(video_url)
        
        if not video_id:
            print("❌ Không thể lấy Video ID. Kiểm tra lại URL!")
            return
        
        optimal_workers = PerformanceOptimizer.calculate_optimal_workers()
        print(f"✅ Video ID: {video_id}")
        print(f"🎯 Số tasks: {optimal_workers:,}")
        print("⚠️  CẢNH BÁO: Số lượng tasks cực lớn có thể gây:")
        print("   - Quá tải mạng")
        print("   - Tiêu thụ CPU cao") 
        print("   - Có thể bị TikTok detect")
        print("🚀 Đang khởi chạy... (Nhấn Ctrl+C để dừng)")
        
        await asyncio.sleep(2)  
        
        await self.init_session()
        self.is_running = True
        self.start_time = time.time()
        
        
        semaphore = asyncio.Semaphore(5000)  # 5000 requests đồng thời
        
        try:
           
            tasks = []
            for i in range(optimal_workers):
                task = asyncio.create_task(self.view_sender(video_id, i, semaphore))
                tasks.append(task)
            
            logger.info(f"✅ Đã khởi tạo {len(tasks):,} tasks")
            
            
            last_display = 0
            while self.is_running:
                await asyncio.sleep(0.5)
                
                current_time = time.time()
                if current_time - last_display >= 3:  
                    stats = self.calculate_stats()
                    print(
                        f"\r✅ Đã gửi: {stats['total_views']:,} | "
                        f"Tốc độ: {stats['views_per_second']:.1f} view/s | "
                        f"Thành công: {stats['success_rate']:.1f}% | "
                        f"Thời gian: {stats['elapsed_time']:.1f}s", 
                        end="", flush=True
                    )
                    last_display = current_time
                    
                    
                    if stats['views_per_second'] > 1500:
                        logger.warning("⚠️  Tốc độ quá cao, xem xét giảm tasks")
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Đang dừng bot...")
        except Exception as e:
            logger.error(f"❌ Lỗi không mong muốn: {e}")
        finally:
            self.is_running = False
            
           
            logger.info("🛑 Đang dừng các tasks...")
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.close_session()
            self.display_stats()

def signal_handler(sig, frame):
    
    print("\n\n🛑 Nhận tín hiệu dừng...")
    sys.exit(0)

async def main():
    
    os.system("cls" if os.name == "nt" else "clear")
    
    print("🚀 TIKTOK VIEW BOT - 100,000 TASKS (CỰC MẠNH)")
    print("=" * 60)
    print("⚠️  CẢNH BÁO: Chỉ sử dụng cho mục đích học tập")
    print("=" * 60)
    
    
    signal.signal(signal.SIGINT, signal_handler)
    
    video_url = input("📥 Nhập link video TikTok: ").strip()
    
    if not video_url.startswith(('http://', 'https://')):
        print("❌ URL không hợp lệ!")
        return
    
   
    try:
        requests.get("https://www.google.com", timeout=5)
    except:
        print("❌ Không có kết nối internet!")
        return
    
    bot = TikTokViewBot()
    
    try:
        await bot.run(video_url)
    except Exception as e:
        logger.error(f"❌ Lỗi chạy bot: {e}")
    finally:
        await bot.close_session()

if __name__ == "__main__":
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        # Tối ưu cho Linux/Mac
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    
    asyncio.set_event_loop(asyncio.new_event_loop())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng chương trình!")