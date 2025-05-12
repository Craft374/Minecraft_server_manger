import customtkinter as ctk
import tkinter.filedialog
from PIL import Image
from ctk_label_button import make_image_button
import asyncio
from mcipc.rcon.je import Client

class ServerFunctions:
    def __init__(self, app):
        self.app = app  # ServerManagerApp 인스턴스를 받아 저장

    def add_server(self):
        print("서버 추가 기능")

    def remove_server(self):
        print("서버 제거 기능")

    def select_server(self, name):
        self.app.log_text.insert("end", f"[INFO] '{name}' 서버 선택됨\n")
        self.app.properties_text.delete("0.0", "end")
        self.app.properties_text.insert("0.0", f"# '{name}'의 server.properties 내용 표시\n")

    def open_folder(self):
        tkinter.filedialog.askdirectory(title="서버 루트 폴더 선택")

    def open_mods_folder(self):
        tkinter.filedialog.askdirectory(title="mods 또는 plugins 폴더 선택")

    def open_settings_window(self):
        settings_win = ctk.CTkToplevel(self.app)
        settings_win.title("설정")
        settings_win.geometry("300x200")

        ctk.CTkLabel(settings_win, text="테마 선택").pack(pady=(20, 5))
        theme_selector = ctk.CTkOptionMenu(settings_win, values=["System", "Light", "Dark"], command=ctk.set_appearance_mode)
        theme_selector.set("Dark")
        theme_selector.pack(pady=5)

        ctk.CTkLabel(settings_win, text="UI 크기 선택").pack(pady=(20, 5))
        scale_selector = ctk.CTkOptionMenu(settings_win, values=["80%", "90%", "100%", "110%", "120%"], command=self.set_ui_scale)
        scale_selector.set("100%")
        scale_selector.pack(pady=5)

    def set_ui_scale(self, scale):
        ctk.set_widget_scaling(int(scale.replace("%", "")) / 100)

    def command_send(self, command):
        with Client("localhost", 25575, passwd="1234") as client:
            response = client.run(command)
            print(f"[RCON 응답]: {response}")

    def kick(self, player_input):
        command = f"kick {player_input.get("1.0", "end-1c").strip()}"
        print(command)
        self.command_send(command)

    def ban(self, player_input):
        command = f"ban {player_input.get("1.0", "end-1c").strip()}"
        print(command)
        self.command_send(command)

    def op(self, player_input):
        command = f"op {player_input.get("1.0", "end-1c").strip()}"
        print(command)
        self.command_send(command)

    def gamemode(self, player_input, mode):
        command = f"gamemode {mode} {player_input.get("1.0", "end-1c").strip()}"
        print(command)
        self.command_send(command)