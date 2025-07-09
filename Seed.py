import asyncio
import aiohttp
import json
from aiohttp_socks import ProxyConnector
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

# ===== КОНФИГУРАЦИЯ =====
SEED_FILE = "seeds.txt"          # Файл с seed-фразами (1 фраза/строка)
PROXY_FILE = "proxies.txt"       # Прокси в формате ip:port:login:password
RESULT_FILE = "result.txt"       # Файл для результатов
ERROR_LOG = "errors.log"          # Лог ошибок
ADDRESSES_PER_SEED = 20           # Количество адресов для проверки на seed
MAX_CONCURRENT_REQUESTS = 10      # Максимум одновременных запросов
# ========================

async def process_seed(seed: str) -> list:
    """Генерирует адреса Ethereum из seed-фразы"""
    addresses = []
    seed_bytes = Bip39SeedGenerator(seed).Generate()
    
    for i in range(ADDRESSES_PER_SEED):
        bip44_ctx = Bip44.FromSeed(
            seed_bytes, 
            Bip44Coins.ETHEREUM
        ).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
        
        addresses.append({
            "address": bip44_ctx.PublicKey().ToAddress(),
            "seed": seed,
            "path": f"m/44'/60'/0'/0/{i}"
        })
    
    return addresses

async def fetch_balance(session: aiohttp.ClientSession, address: str, proxy: str) -> dict:
    """Проверяет баланс через Blockscan API"""
    url = f"https://api.blockscan.com/api?module=account&action=balancemulti&address={address}&tag=latest&apikey=freekey"
    
    try:
        async with session.get(url, proxy=proxy, timeout=30) as response:
            data = await response.json()
            return data.get("result", [])
    except Exception as e:
        return {"error": str(e)}

async def worker(session: aiohttp.ClientSession, queue: asyncio.Queue, proxy: str):
    """Обрабатывает задачи из очереди"""
    while not queue.empty():
        try:
            wallet = await queue.get()
            balances = await fetch_balance(session, wallet["address"], proxy)
            
            if isinstance(balances, list):
                for asset in balances:
                    if float(asset["balance"]) > 0:
                        with open(RESULT_FILE, "a") as f:
                            f.write(f"[{asset['blockchain']}] {asset['balance']} {asset['symbol']} | {wallet['address']} | {wallet['seed']} | {wallet['path']}\n")
        except Exception as e:
            with open(ERROR_LOG, "a") as log:
                log.write(f"Ошибка: {e}\n")
        finally:
            queue.task_done()

async def main():
    # Инициализация файлов
    open(RESULT_FILE, "w").close()
    open(ERROR_LOG, "w").close()
    
    # Загрузка прокси
    with open(PROXY_FILE) as f:
        proxies = [f"http://{line.strip()}" for line in f if line.strip()]
    
    # Генерация адресов
    tasks = []
    with open(SEED_FILE) as f:
        for seed in f:
            if seed.strip():
                tasks.append(process_seed(seed.strip()))
    
    wallets = []
    for future in asyncio.as_completed(tasks):
        wallets.extend(await future)
    
    # Создание очереди задач
    queue = asyncio.Queue()
    for wallet in wallets:
        await queue.put(wallet)
    
    # Запуск воркеров
    async with aiohttp.ClientSession(
        connector=ProxyConnector.from_url(proxies[0]), 
        headers={"User-Agent": "Mozilla/5.0"}
    ) as session:
        workers = [
            worker(session, queue, random.choice(proxies))
            for _ in range(MAX_CONCURRENT_REQUESTS)
        ]
        await asyncio.gather(*workers)

if __name__ == "__main__":
    asyncio.run(main())