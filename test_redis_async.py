
import asyncio
import redis.asyncio as redis


async def test_redis():
    client = redis.Redis.from_url(
        "redis://localhost:6379/0"
    )

    try:
        print("Redis ping:", await client.ping())
        print(
            "Redis version:",
            (await client.info("server"))["redis_version"]
        )
    finally:
        await client.aclose()


asyncio.run(test_redis())
