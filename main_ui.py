import customtkinter as ctk
from sub_process import ServerFunctions
from PIL import Image
from ctk_label_button import make_image_button

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
font = "Noto Sans KR"

class ServerManagerApp(ctk.CTk):
    def tab_1(self):
        # 탭 1: 설정 편집
        self.tabview.add("상태")
        tab = self.tabview.tab("상태")
        tab.grid_rowconfigure(7, weight=1)
        tab.grid_columnconfigure(2, weight=1)

        self.tab_bg_canvas = ctk.CTkCanvas(tab, bg="#1D1E1E", highlightthickness=0, width=1920,height=1920)
        self.tab_bg_canvas.grid(row=0, column=0, rowspan=8, columnspan=8, sticky="nsew", padx=5, pady=5)

        container_1 = ctk.CTkFrame(tab, fg_color="#1D1E1E", border_color="#1D1E1E") # 서버상태+온라인 글씨 정렬용 컨테이너
        container_1.grid(row=0, column=0, padx=10, pady=(20, 0), sticky="nw")

        self.server_condition_title = ctk.CTkLabel(container_1, text="서버 상태: ", font=(font, 30), fg_color="#1D1E1E")
        self.server_condition_title.grid(row=0, column=0, sticky="nw")

        self.server_condition = ctk.CTkLabel(container_1, text="온라인", font=(font, 30), text_color="turquoise", fg_color="#1D1E1E")
        self.server_condition.grid(row=0, column=1, sticky="nw")

        self.server_start_btn = ctk.CTkButton(container_1, text="서버 시작", font=(font, 30), width=175, height=50)
        self.server_start_btn.grid(row=0,column=2, rowspan=2, sticky="w", padx=(30,2000))

        container_in1 = ctk.CTkFrame(container_1, fg_color="#1D1E1E") # 체크박스 + 글씨 정렬용 컨테이너
        container_in1.grid(row=1, column=0, sticky="nw",columnspan=2)

        self.no_gui_checkbox = ctk.CTkCheckBox(container_in1, bg_color="#1D1E1E", text="",width=0)
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
        self.command_input = ctk.CTkTextbox(tab, height=50, font=(font, 30))
        self.command_input.grid(row=1, column=0, padx=(5, 0), pady=(10,5), sticky="ew")

        send_img = ctk.CTkImage(Image.open("plane.png"), size=(35, 35))

        # 전송 버튼 (하단 오른쪽)
        self.send = ctk.CTkButton(tab, width=50, height=50, text="", image=send_img, fg_color="white", anchor="center")
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

        self.op_btn = ctk.CTkButton(tab, text="op", bg_color="#1D1E1E", width=75, height=30,
                                    command=lambda: self.sub.op(self.player_input))
        self.op_btn.grid(row=4, column=0, columnspan=2, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.gamemode_btn = ctk.CTkButton(tab, text="gamemode", bg_color="#1D1E1E", width=75, height=30,
                                          command=lambda: self.sub.gamemode(self.player_input, self.gamemode_option.get()))
        self.gamemode_btn.grid(row=5, column=0, padx=(10, 5), pady=(10, 5), sticky="e")

        self.gamemode_option = ctk.CTkOptionMenu(tab, values=["survival", "creative", "adventure", "spectator"],
                                                 width=100, height=30, dynamic_resizing=False, bg_color="#1D1E1E")
        self.gamemode_option.grid(row=5, column=1, padx=(5, padx_global), pady=(10, 5), sticky="w")

        padx_global2 = 20
        self.text_2 = ctk.CTkLabel(tab, text="월드 관련 명령어", font=(font, 30), fg_color="#1D1E1E")
        self.text_2.grid(row=0, column=2, columnspan=2, padx=(10, padx_global2), pady=(10, 0), sticky="w")

        self.time_btn = ctk.CTkButton(tab, text="time set", width=75, height=30, bg_color="#1D1E1E")
        self.time_btn.grid(row=1, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.time_input = ctk.CTkTextbox(tab, height=30, font=(font, 15), fg_color="white",
                                         text_color="black", width=100, wrap='none', bg_color="#1D1E1E",
                                         activate_scrollbars=False)
        self.time_input.insert("1.0", "숫자")
        self.time_input.grid(row=1, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.wetaher_btn = ctk.CTkButton(tab, text="weather", width=75, height=30, bg_color="#1D1E1E")
        self.wetaher_btn.grid(row=2, column=2, padx=(10, 0), pady=(10, 5), sticky="")

        self.weather_option = ctk.CTkOptionMenu(tab, values=["clear", "rain", "thunder"], width=100,
                                                height=30, dynamic_resizing=False, bg_color="#1D1E1E")
        self.weather_option.grid(row=2, column=3, padx=(10, padx_global2), pady=(10, 5), sticky="w")

        self.text_3 = ctk.CTkLabel(tab, text="서버 관련 명령어", font=(font, 30), fg_color="#1D1E1E")
        self.text_3.grid(row=0, column=4, padx=(10, 0), pady=(10, 0), sticky="w")

        self.reload_btn = ctk.CTkButton(tab, text="reload", bg_color="#1D1E1E", width=75, height=30)
        self.reload_btn.grid(row=1, column=4, padx=(10, padx_global), pady=(10, 5), sticky="")

        self.plugins_btn = ctk.CTkButton(tab, text="plugins", bg_color="#1D1E1E", width=75, height=30)
        self.plugins_btn.grid(row=2, column=4, padx=(10, padx_global), pady=(10, 5), sticky="")

    def __init__(self):
        super().__init__()
        self.title("EMSR")
        self.geometry("1000x600")
        self.resizable(False, False)
        # self.resizable(True, True)

        self.sub = ServerFunctions(self)  # ServerFunctions 연결

        img_size = 60
        folder_img = ctk.CTkImage(Image.open("Group 12.png"), size=(img_size,img_size))

        # 서버 목록 프레임
        self.server_list_frame = ctk.CTkFrame(self, width=200)
        self.server_list_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.server_label = ctk.CTkLabel(self.server_list_frame, text="서버 목록", font=ctk.CTkFont(size=16, weight="bold"), width=10)
        self.server_label.pack(pady=(10, 10))

        self.server_buttons = []
        for name in ["paper-1.20", "modded-1.16", "fabric-test"]:
            btn = ctk.CTkButton(self.server_list_frame, text=name, command=lambda n=name: self.func.select_server(n))
            btn.pack(pady=5, fill="x", padx=5)
            self.server_buttons.append(btn)

        # 서버 관리 버튼 하단 정렬 프레임
        self.server_btn_frame = ctk.CTkFrame(self.server_list_frame, fg_color="transparent")
        self.server_btn_frame.pack(side="bottom", anchor="w", padx=5, pady=10)

        # 버튼 공통 스타일
        button_size = 50

        self.add_server_btn = ctk.CTkButton(
            self.server_btn_frame, text="+", width=button_size, height=button_size,anchor="center",
            command=self.sub.add_server, font=(font, 30))
        self.add_server_btn.pack(side="left", padx=(0, 5))

        self.test_img = make_image_button(self.server_btn_frame, "Group 12.png", lambda: print("d"), size=(50, 50))
        self.test_img.configure(width=50,height=50)
        self.test_img.pack(side="left", padx=(0, 5))

        self.settings_btn = ctk.CTkButton(
            self.server_btn_frame, text="⚙", width=button_size, height=button_size,anchor="center",
            command=self.sub.open_settings_window, font=(font, 30))
        self.settings_btn.pack(side="left", padx=5)

        # 오른쪽 탭뷰
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=(0, 10), pady=10)

        # 탭 1: 설정 편집
        self.tab_1()

        # 탭 2: 로그 출력 + 명령어 입력
        self.tab_2()

        # 탭 3: 작업 버튼
        self.tab_3()

        # frame = ctk.CTkFrame(self.tabview.tab("유틸"))
        # frame.pack(pady=20)
        self.tabview.add("관리")



        # ctk.CTkButton(frame, text="서버 시작", width=200).pack(pady=5)
        # ctk.CTkButton(frame, text="서버 중지", width=200).pack(pady=5)
        # ctk.CTkButton(frame, text="폴더 열기", width=200, command=self.func.open_folder).pack(pady=5)
        # ctk.CTkButton(frame, text="모드 폴더 열기", width=200, command=self.func.open_mods_folder).pack(pady=5)
if __name__ == "__main__":
    app = ServerManagerApp()
    app.mainloop()
