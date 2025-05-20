from mcstatus import JavaServer

server = JavaServer.lookup("127.0.0.1:25565")  # 주소와 포트

status = server.status()
print("MOTD:", status.description)
print("현재 접속자 수:", status.players.online)
print("최대 접속자 수:", status.players.max)
print("접속 중 플레이어:", status.players.sample)  # 일부 플레이어 리스트

print(f"버전: {status.version.name}")
print(f"motd: {status.description}")
print(f"현재 플레이어 수: {status.players.online} / {status.players.max}")

# # query는 별도 호출 필요
# query = server.query()
# print(f"플랫폼: {query.software.version}")