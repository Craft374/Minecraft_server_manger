import time
import customtkinter as ctk
from sub_process import ServerFunctions
from ui_create_server import Server_create
from PIL import Image
from ctk_label_button import make_image_button
from mcipc.rcon.je import Client
import threading
from mcstatus import JavaServer
import subprocess
import sys
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
font = "Noto Sans KR"

if sys.platform.startswith("darwin"):
    win = 0
elif sys.platform.startswith("win"):
    win = 1
else:
    win = -1

class ServerManagerApp(ctk.CTk):
    def RCON(self):
        try:
            with Client("localhost", 25575, passwd="1234") as client:
                # 메모리
                used = client.run("print memory").splitlines()[0].split(',')[0]
                total = client.run("print memory").splitlines()[0].split(',')[2]
                self.server_memory.configure(text=f"현재 메모리: {used}mb / {total}mb")

                # tps
                tps = client.run("print tps").split(',')
                self.server_tps.configure(text=f"현재 tps: {tps[0]}, {tps[1]}, {tps[2].replace("\n", "")}")

                # 온라인
                self.server_condition.configure(text="온라인", text_color="turquoise")

                # mc_stat
                server = JavaServer.lookup("127.0.0.1:25565")  # 주소와 포트
                status = server.status()
                self.server_motd.configure(text=f"motd: {status.description}")
                self.server_player.configure(text=f"현재 플레이어 수: {status.players.online} / {status.players.max}")

                # mc_stat query
                try:
                    query = server.query()
                    self.server_version.configure(text=f"버전: {query.software.version}")
                    self.server_platform.configure(text=f"플랫폼: {query.software.brand}")
                except:
                    try:
                        info = client.run("print info").split(',')
                        self.server_version.configure(text=f"버전: {info[0]}")
                        self.server_platform.configure(text=f"플랫폼: {info[1]}")
                    except:
                        self.server_version.configure(text="버전:조회 실패")
                        self.server_platform.configure(text="플랫폼: 조회 실패")

        except:
            self.server_memory.configure(text="현재 메모리: 조회 실패")
            self.server_tps.configure(text="현재 tps: 조회 실패")
            self.server_condition.configure(text="오프라인", text_color="red")
            self.server_version.configure(text="버전:조회 실패")
            self.server_platform.configure(text="플랫폼: 조회 실패")
            self.server_motd.configure(text="motd: 조회 실패")
            self.server_player.configure(text="현재 플레이어 수: 조회 실패")

    def update_memory(self):
        threading.Thread(target=self.RCON).start()
        self.after(1000, self.update_memory)

    def toggle_server(self):
        if self.select_server:
            if not self.server_running:
                self.start_server()
                self.server_start_btn.configure(text="서버 정지", fg_color="red", hover_color="brown")
                self.server_running = True
            else:
                self.server_start_btn.configure(state="disabled")
                threading.Thread(target=self.stop_server, daemon=True).start()
                self.server_running = False

    def start_server(self):
        def run_server():
            base_path = os.path.expanduser("~/Documents/Minecraft_server")
            server_path = f"{base_path}/{self.server_name}"

            self.server_process = subprocess.Popen(
                ["/bin/bash", f"{server_path}/run.sh"],  # 직접 bash로 실행
                cwd=server_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in self.server_process.stdout:
                if "Thread RCON Client" in line:
                    continue
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")

        threading.Thread(target=run_server, daemon=True).start()

    def stop_server(self):
        if self.server_process:
            if self.server_process.poll() is None:
                try:
                    with Client("localhost", 25575, passwd="1234") as client:
                        client.run("save-all")
                        client.run("stop")
                    try:
                        self.server_process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        self.server_process.terminate()
                        try:
                            self.server_process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            pass  # 최악의 경우 무시
                finally:
                    self.server_process = None
                    self.server_start_btn.configure(text="서버 시작", fg_color="#206BA5", hover_color="#144770",
                                                    state="normal")
            else:
                self.server_process = None
                self.server_start_btn.configure(text="서버 시작", fg_color="#206BA5", hover_color="#144770", state="normal")
        else:
            self.server_start_btn.configure(text="서버 시작", fg_color="#206BA5", hover_color="#144770", state="normal")

    def server_select(self, name):
        self.select_server = True
        print(name)
        self.server_name = name
        self.server_name_label.configure(text=f"현재 선택된 서버:\n{name.split('/')[2]}")

    def tab_1(self):
        # 탭 1: 설정 편집
        self.tabview.add("상태")
        tab = self.tabview.tab("상태")
        tab.grid_rowconfigure(7, weight=1)
        tab.grid_columnconfigure(2, weight=1)

        self.tab_bg_canvas = ctk.CTkCanvas(tab, bg="#1D1E1E", highlightthickness=0, width=1920, height=1920)
        self.tab_bg_canvas.grid(row=0, column=0, rowspan=8, columnspan=8, sticky="nsew", padx=5, pady=5)

        container_1 = ctk.CTkFrame(tab, fg_color="#1D1E1E", border_color="#1D1E1E") # 서버상태+온라인 글씨 정렬용 컨테이너
        container_1.grid(row=0, column=0, padx=10, pady=(20, 0), sticky="nw")

        self.server_condition_title = ctk.CTkLabel(container_1, text="서버 상태: ", font=(font, 30), fg_color="#1D1E1E")
        self.server_condition_title.grid(row=0, column=0, sticky="nw")

        self.server_condition = ctk.CTkLabel(container_1, text="온라인", font=(font, 30), text_color="turquoise", fg_color="#1D1E1E", width=150,  anchor="w")
        self.server_condition.grid(row=0, column=1, sticky="w")

        self.server_start_btn = ctk.CTkButton(container_1, text="서버 시작", font=(font, 30), width=175, height=50, command=self.toggle_server)
        self.server_start_btn.grid(row=0,column=2, rowspan=2, sticky="w", padx=(30,2000))

        container_in1 = ctk.CTkFrame(container_1, fg_color="#1D1E1E") # 체크박스 + 글씨 정렬용 컨테이너
        container_in1.grid(row=1, column=0, sticky="nw",columnspan=2)

        self.no_gui_checkbox = ctk.CTkCheckBox(container_in1, bg_color="#1D1E1E", text="",width=0,command=lambda: self.sub.nogui_toggle(self.no_gui_checkbox.get(), self.server_name, win) if self.select_server else None)
        self.no_gui_checkbox.grid(row=0,column=0,sticky="nw",pady=(20,10))

        self.server_checkbox_text = ctk.CTkLabel(container_in1, text="nogui", font=(font, 30), fg_color="#1D1E1E")
        self.server_checkbox_text.grid(row=0, column=1, sticky="nw",pady=(10,10))

        self.server_player = ctk.CTkLabel(tab, text="현재 플레이어 수: 0 / 20", font=(font, 30), fg_color="#1D1E1E")
        self.server_player.grid(row=2, column=0, sticky="nw", padx=10, pady=10, columnspan=3)

        self.server_memory = ctk.CTkLabel(tab, text="현재 메모리: 8612mb / 20443mb", font=(font, 30), fg_color="#1D1E1E")
        self.server_memory.grid(row=3, column=0, sticky="nw", padx=10, pady=10, columnspan=3)

        self.server_tps = ctk.CTkLabel(tab, text="현재 tps: 19.9, 20, 20", font=(font, 30), fg_color="#1D1E1E")
        self.server_tps.grid(row=4, column=0, sticky="nw", padx=10, pady=10, columnspan=3)

        self.server_version = ctk.CTkLabel(tab, text="버전: 1.20.1", font=(font, 30), fg_color="#1D1E1E")
        self.server_version.grid(row=5, column=0, sticky="nw", padx=10, pady=10, columnspan=3)

        self.server_platform = ctk.CTkLabel(tab, text="플랫폼: Forge", font=(font, 30), fg_color="#1D1E1E")
        self.server_platform.grid(row=6, column=0, sticky="nw", padx=10, pady=10, columnspan=3)

        self.server_motd = ctk.CTkLabel(tab, text="motd: 이 서버는 무려 섭어입니다+", font=(font, 30), fg_color="#1D1E1E")
        self.server_motd.grid(row=7, column=0, sticky="nw", padx=10, pady=10, columnspan=2)

        self.update_memory()

    def tab_2(self):
        self.tabview.add("콘솔")
        tab = self.tabview.tab("콘솔")

        # 탭 그리드 공간 분배 설정
        tab.grid_rowconfigure(0, weight=1)  # log_text가 공간을 다 먹게
        tab.grid_rowconfigure(1, weight=0)  # command_input은 고정 높이
        tab.grid_columnconfigure(0, weight=1)  # command_input이 늘어나게
        tab.grid_columnconfigure(1, weight=0)  # 버튼은 고정 크기

        # 로그 출력창 (전체 상단 영역)
        self.log_text = ctk.CTkTextbox(tab,state="disabled")
        self.log_text.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=(5, 0))

        # 명령어 입력창 (하단 왼쪽)
        self.command_input = ctk.CTkEntry(tab, font=(font, 30), fg_color="#1D1E1E", border_color="gray", border_width=1, height=50)
        self.command_input.grid(row=1, column=0, padx=(5, 0), pady=(10, 5), sticky="ew")
        # self.command_input.bind("<Return>", lambda event: self.sub.command_send(self.command_input.get().strip()))

        self.command_history = []  # 이전 명령 저장 리스트
        self.command_index = -1  # 현재 히스토리 탐색 위치

        def on_enter(event):
            command = self.command_input.get().strip()
            if command:
                self.sub.command_send(command)
                self.command_history.append(command)
                self.command_index = -1
                self.command_input.delete(0, "end")

        def on_up_arrow(event):
            if self.command_history:
                if self.command_index == -1:
                    self.command_index = len(self.command_history) - 1
                elif self.command_index > 0:
                    self.command_index -= 1

                prev_command = self.command_history[self.command_index]
                self.command_input.delete(0, "end")
                self.command_input.insert(0, prev_command)

        def on_down_arrow(event):
            if self.command_history and self.command_index != -1:
                if self.command_index < len(self.command_history) - 1:
                    self.command_index += 1
                    next_command = self.command_history[self.command_index]
                    self.command_input.delete(0, "end")
                    self.command_input.insert(0, next_command)
                else:
                    self.command_index = -1
                    self.command_input.delete(0, "end")

        # 바인딩
        self.command_input.bind("<Return>", on_enter)
        self.command_input.bind("<Up>", on_up_arrow)
        self.command_input.bind("<Down>", on_down_arrow)

        send_img = ctk.CTkImage(Image.open("image/plane.png"), size=(35, 35))

        # 전송 버튼 (하단 오른쪽)
        self.send = ctk.CTkButton(tab, width=50, height=50, text="", image=send_img, fg_color="white", anchor="center",
                                   command=lambda: self.sub.command_send(self.command_input.get().strip()))
        self.send.grid(row=1, column=1, padx=5, pady=(10,5), sticky="e")

    def tab_3(self):
        self.tabview.add("유틸")
        tab = self.tabview.tab("유틸")

        tab.grid_rowconfigure(7, weight=1)
        tab.grid_columnconfigure(4, weight=1)

        self.tab_bg_canvas = ctk.CTkCanvas(tab, bg="#1D1E1E", highlightthickness=0, width=1920, height=1920)
        self.tab_bg_canvas.grid(row=0, column=0, rowspan=8, columnspan=8, sticky="nsew", padx=5, pady=5)

        padx_global = 20
        self.text_1 = ctk.CTkLabel(tab, text="플레이어 관련 명령어", font=(font, 30), fg_color="#1D1E1E", bg_color="#1D1E1E")
        self.text_1.grid(row=0, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 0), sticky="ew")

        self.player_input = ctk.CTkTextbox(tab, font=(font, 15), fg_color="white",
                                           text_color="black", height=30, width=150, wrap='none',
                                           activate_scrollbars=False, bg_color="#1D1E1E")
        self.player_input.insert("1.0", "플레이어 이름")
        self.player_input.grid(row=1, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.kick_btn = ctk.CTkButton(tab, text="kick", bg_color="#1D1E1E", width=75, height=30,
                                      command=lambda: self.sub.kick(self.player_input))
        self.kick_btn.grid(row=2, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.ban_btn = ctk.CTkButton(tab, text="ban", bg_color="#1D1E1E", width=75, height=30,
                                     command=lambda: self.sub.ban(self.player_input))
        self.ban_btn.grid(row=3, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.pardon_btn = ctk.CTkButton(tab, text="pardon", bg_color="#1D1E1E", width=75, height=30,
                                    command=lambda: self.sub.pardon(self.player_input))
        self.pardon_btn.grid(row=4, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.op_btn = ctk.CTkButton(tab, text="op", bg_color="#1D1E1E", width=75, height=30,
                                    command=lambda: self.sub.op(self.player_input))
        self.op_btn.grid(row=5, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.deop_btn = ctk.CTkButton(tab, text="deop", bg_color="#1D1E1E", width=75, height=30,
                                    command=lambda: self.sub.deop(self.player_input))
        self.deop_btn.grid(row=6, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.gamemode_btn = ctk.CTkButton(tab, text="gamemode", bg_color="#1D1E1E", width=75, height=30,
                                          command=lambda: self.sub.gamemode(self.player_input, self.gamemode_option.get()))
        self.gamemode_btn.grid(row=7, column=0, padx=(10, 5), pady=(10, 5), sticky="ne")

        self.gamemode_option = ctk.CTkOptionMenu(tab, values=["survival", "creative", "adventure", "spectator"],
                                                 width=100, height=30, dynamic_resizing=False, bg_color="#1D1E1E")
        self.gamemode_option.grid(row=7, column=1, padx=(5, padx_global), pady=(10, 5), sticky="nw")

        # 2번쨰 열
        padx_global2 = 20
        self.text_2 = ctk.CTkLabel(tab, text="월드 관련 명령어", font=(font, 30), fg_color="#1D1E1E")
        self.text_2.grid(row=0, column=2, columnspan=2, padx=(10, padx_global2), pady=(10, 0), sticky="w")

        self.time_btn = ctk.CTkButton(tab, text="time set", width=75, height=30, bg_color="#1D1E1E",
                                    command=lambda: self.sub.time(self.time_input))
        self.time_btn.grid(row=1, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.time_input = ctk.CTkTextbox(tab, height=30, font=(font, 15), fg_color="white",
                                         text_color="black", width=100, wrap='none', bg_color="#1D1E1E",
                                         activate_scrollbars=False)
        self.time_input.insert("1.0", "숫자 & 시간대")
        self.time_input.grid(row=1, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.wetaher_btn = ctk.CTkButton(tab, text="weather", width=75, height=30, bg_color="#1D1E1E",
                                        command=lambda: self.sub.weather(self.weather_option.get()))
        self.wetaher_btn.grid(row=2, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.weather_option = ctk.CTkOptionMenu(tab, values=["clear", "rain", "thunder"], width=100,
                                                height=30, dynamic_resizing=False, bg_color="#1D1E1E")
        self.weather_option.grid(row=2, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.gamerule_option = ctk.CTkOptionMenu(tab, values=["announceAdvancements", "commandBlockOutput", "commandModificationBlockLimit (1.20.3+)",
                                                              "disableElytraMovementCheck", "disableRaids (1.14+)", "doDaylightCycle",
                                                              "doEntityDrops (1.11+)", "doFireTick", "doImmediateRespawn (1.15+)", "doInsomnia (1.14+)",
                                                              "doLimitedCrafting", "doMobLoot", "doMobSpawning", "doPatrolSpawning (1.14+)",
                                                              "doSpectatorGenerateChunks (1.19.3+)", "doTileDrops", "doTraderSpawning (1.14+)",
                                                              "doWardenSpawning (1.19+)", "doWeatherCycle", "forgiveDeadPlayers (1.15+)",
                                                              "gameLoopFunction (1.12+)", "globalSoundEvents (1.20.3+)", "keepInventory",
                                                              "logAdminCommands", "maxCommandChainLength", "maxEntityCramming (1.11+)", "mobGriefing",
                                                              "naturalRegeneration", "playersSleepingPercentage (1.17+)", "randomTickSpeed", "reducedDebugInfo",
                                                              "sendCommandFeedback", "showDeathMessages", "spawnRadius", "spectatorsGenerateChunks",
                                                              "universalAnger (1.16+)"], width=100, height=30, dynamic_resizing=False, bg_color="#1D1E1E")

        self.gamerule_option.grid(row=3, column=2, columnspan=2,padx=(15, padx_global2+5), pady=(10, 5), sticky="we")

        self.gamerule_btn = ctk.CTkButton(tab, text="gamerule", width=75, height=30, bg_color="#1D1E1E",
                                        command=lambda: self.sub.gamerule(self.gamerule_option.get(), self.gamerule_input))
        self.gamerule_btn.grid(row=4, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.gamerule_input = ctk.CTkTextbox(tab, height=30, font=(font, 15), fg_color="white",
                                         text_color="black", width=100, wrap='none', bg_color="#1D1E1E",
                                         activate_scrollbars=False)
        self.gamerule_input.insert("1.0", "인수")
        self.gamerule_input.grid(row=4, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.difficulty_btn = ctk.CTkButton(tab, text="difficulty", width=75, height=30, bg_color="#1D1E1E",
                                        command=lambda: self.sub.difficult(self.difficulty_option.get()))
        self.difficulty_btn.grid(row=5, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.difficulty_option = ctk.CTkOptionMenu(tab, values=["peaceful", "easy", "normal", "hard"], width=100,
                                                height=30, dynamic_resizing=False, bg_color="#1D1E1E")
        self.difficulty_option.grid(row=5, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.text_2 = ctk.CTkLabel(tab, text="인수: true & false 혹은 숫자", font=(font, 15), fg_color="#1D1E1E",  bg_color="#1D1E1E")
        self.text_2.grid(row=6, column=2, columnspan=2, padx=(15, padx_global2+5), pady=(10, 0), sticky="nwe")

        self.text_2 = ctk.CTkLabel(tab, text="시간: day, night, noon, \nmidnight, sunrise, sunset", font=(font, 15), fg_color="#1D1E1E",  bg_color="#1D1E1E")
        self.text_2.grid(row=7, column=2, columnspan=2, padx=(15, padx_global2+5), pady=(10, 0), sticky="nwe")

        # 3번째 열
        self.text_3 = ctk.CTkLabel(tab, text="서버 관련 명령어", font=(font, 30), fg_color="#1D1E1E")
        self.text_3.grid(row=0, column=4, padx=(10, 0), pady=(10, 0), sticky="w")

        self.reload_btn = ctk.CTkButton(tab, text="reload", bg_color="#1D1E1E", width=75, height=30, command=self.sub.reload)
        self.reload_btn.grid(row=1, column=4, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.plugins_btn = ctk.CTkButton(tab, text="stop", bg_color="#1D1E1E", width=75, height=30, command=self.sub.stop)
        self.plugins_btn.grid(row=2, column=4, padx=(10, padx_global), pady=(10, 5), sticky="")

    def side_bar(self):
        self.server_list = self.sub.server_list()
        print(self.server_list)

        self.server_list_frame = ctk.CTkFrame(self, width=200)
        self.server_list_frame.pack(side="left", fill="y", padx=10, pady=10)

        # 배경용 프레임
        self.server_name_bg = ctk.CTkFrame(self.server_list_frame, fg_color="#1D1E1E", corner_radius=5)
        self.server_name_bg.pack(pady=(10, 10), fill="x", padx=5)

        # 라벨을 배경 프레임 위에 생성
        self.server_name_label = ctk.CTkLabel(self.server_name_bg, text="현재 선택된 서버:\nNone",font=ctk.CTkFont(size=16, weight="bold"))
        self.server_name_label.pack(padx=10, pady=5, fill="x")

        self.server_label = ctk.CTkLabel(self.server_list_frame, text="서버 목록", font=ctk.CTkFont(size=18, weight="bold"),
                                         width=10)
        self.server_label.pack(pady=(5, 10))

        self.server_buttons = []
        for name in self.server_list:
            btn = ctk.CTkButton(self.server_list_frame, text=name, command=lambda n=name: self.server_select(n))
            btn.pack(pady=5, fill="x", padx=5)
            self.server_buttons.append(btn)

        # 서버 관리 버튼 하단 정렬 프레임
        self.server_btn_frame = ctk.CTkFrame(self.server_list_frame, fg_color="transparent")
        self.server_btn_frame.pack(side="bottom", anchor="w", padx=5, pady=10)

        # 버튼 공통 스타일
        button_size = 50

        self.add_server_btn = ctk.CTkButton(
            self.server_btn_frame, text="+", width=button_size, height=button_size, anchor="center",
            command=self.create.open_create_window, font=(font, 30))
        self.add_server_btn.pack(side="left", padx=(0, 5))

        self.test_img = make_image_button(self.server_btn_frame, "image/Group 12.png", lambda: print("d"),
                                          size=(50, 50))
        self.test_img.configure(width=50, height=50)
        self.test_img.pack(side="left", padx=(0, 5))

        self.settings_btn = ctk.CTkButton(
            self.server_btn_frame, text="⚙", width=button_size, height=button_size, anchor="center",
            command=self.sub.open_settings_window, font=(font, 30))
        self.settings_btn.pack(side="left", padx=5)

    def __init__(self):
        super().__init__()
        self.title("EMSR")
        self.geometry("1000x600")
        self.resizable(False, False)
        # self.resizable(True, True)
        self.server_running = False
        self.server_process = None
        self.select_server =False
        self.server_name = ""

        self.sub = ServerFunctions(self)  # ServerFunctions 연결
        self.create = Server_create(self)

        img_size = 60
        folder_img = ctk.CTkImage(Image.open("image/Group 12.png"), size=(img_size,img_size))

        # 서버 목록 프레임
        self.side_bar()

        # 오른쪽 탭뷰
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=(0, 10), pady=10)

        # 탭 1: 설정 편집
        self.tab_1()

        # 탭 2: 로그 출력 + 명령어 입력
        self.tab_2()

        # 탭 3: 작업 버튼
        self.tab_3()

        self.tabview.add("관리")
if __name__ == "__main__":
    if not win == -1:
        app = ServerManagerApp()
        app.mainloop()
