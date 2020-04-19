import discord, os, asyncio, aiomysql

async def run_command(command):
    output = None

    host = os.environ.get("DB_HOST_URL")
    port = os.environ.get("DB_PORT")
    username = os.environ.get("DB_USERNAME")
    password = os.environ.get("DB_PASSWORD")
    db = os.environ.get("DB_NAME")

    pool = await aiomysql.create_pool(host=host, port=int(port),
                                      user=username, password=password,
                                      db=db)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(command)
            await conn.commit()
            output = await cur.fetchall()
            
    pool.close()
    await pool.wait_closed()

    return output