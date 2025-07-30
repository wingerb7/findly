import redis
import os

# Config (zelfde als in je project)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Verbinden
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

try:
    # Testverbinding
    pong = r.ping()
    print(f"✅ Verbonden met Redis: {pong}")

    # Testwaarde opslaan
    r.set("test_key", "Hallo Redis!", ex=10)  # TTL = 10 sec
    value = r.get("test_key")
    print(f"Opgeslagen waarde: {value}")

except Exception as e:
    print(f"❌ Fout bij verbinden met Redis: {e}")