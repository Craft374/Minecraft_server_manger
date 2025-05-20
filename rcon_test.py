import asyncio
from mcipc.rcon.je import Client
import time

async def spam_and_shutdown():
    try:
        with Client("localhost", 25575, passwd="1234") as client:
            response = client.run("print memory")
            line = response.splitlines()[0]  # 첫 줄만 가져오기
            items = line.split(',')  # 쉼표로 분리
            print(items[0])
            print(client.run("print memory").splitlines()[0].split(',')[0])
            response = client.run("print tps").split(',')
            print(response[0])
    except Exception as e:
        print("RCON 연결 실패:", e)

asyncio.run(spam_and_shutdown())
