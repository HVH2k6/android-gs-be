"""
Clear Redis blacklist keys
"""
import asyncio
import redis.asyncio as redis

async def clear_blacklist():
    try:
        r = await redis.from_url("redis://localhost:6379", decode_responses=True)
        keys = []
        async for key in r.scan_iter(match="blacklist:refresh:*"):
            keys.append(key)

        if keys:
            print(f"Found {len(keys)} blacklisted tokens")
            await r.delete(*keys)
            print(f"Cleared {len(keys)} tokens")
        else:
            print("No blacklisted tokens found")

        await r.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(clear_blacklist())
    print("Done!")
