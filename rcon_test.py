import asyncio
from mcipc.rcon.je import Client

async def spam_and_shutdown():
    try:
        with Client("localhost", 25575, passwd="1234") as client:
            # 2초마다 say s → 0, 2, 4초에 총 3회 전송
            response = client.run("stop")
            print(response)

    except Exception as e:
        print("RCON 연결 실패:", e)

asyncio.run(spam_and_shutdown())
