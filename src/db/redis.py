from redis import asyncio as aioredis
from src.config import Config

JWT_EXPIRY = 3600

token_block_list = aioredis.from_url(Config.REDIS_URL)


async def add_jti_to_blocklist(jti: str) -> None:
    await token_block_list.set(name=jti, value="", ex=JWT_EXPIRY)


async def token_in_blocklist(jti: str) -> bool:
    jti = await token_block_list.get(jti)
    # 1st method
    """
    return True if jti is not None else False
    """
    # 2nd method
    """ 
    if jti is not None:
        return True
    else:
        return False
    """
    return jti is not None
