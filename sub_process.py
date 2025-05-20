import customtkinter as ctk
import tkinter.filedialog
from PIL import Image
from ctk_label_button import make_image_button
from mcipc.rcon.je import Client
import os
import re

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
        try:
            with Client("localhost", 25575, passwd="1234") as client:
                response = client.run(command)
                for line in response.splitlines():
                    if "Thread RCON Client" in line:
                        continue
                    self.app.log_text.configure(state="normal")
                    self.app.log_text.insert("end", line + "\n")
                    self.app.log_text.see("end")
                    self.app.log_text.configure(state="disabled")
        except Exception as e:
            self.app.log_text.configure(state="normal")
            self.app.log_text.insert("end", f"RCON 연결 실패: {e}\n")
            self.app.log_text.see("end")
            self.app.log_text.configure(state="disabled")

    def kick(self, player_input):
        command = f"kick {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def ban(self, player_input):
        command = f"ban {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def op(self, player_input):
        command = f"op {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def deop(self, player_input):
        command = f"deop {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def pardon(self, player_input):
        command = f"pardon {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def gamemode(self, player_input, mode):
        command = f"gamemode {mode} {player_input.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def time(self, time):
        command = f"time set {time.get("1.0", "end-1c").strip()}"
        self.command_send(command)

    def weather(self, weather):
        command = f"weather {weather}"
        self.command_send(command)

    def reload(self):
        command = "reload confirm"
        self.command_send(command)

    def stop(self):
        command = "save-all"
        self.command_send(command)
        command = "stop"
        self.command_send(command)

    def gamerule(self, rule, arg):
        rule = rule.split(" (")[0]  # 괄호 포함 버전 정보 제거
        command = f"gamerule {rule} {arg.get('1.0', 'end-1c').strip()}"
        self.command_send(command)

    def difficult(self, dif):
        command = f"difficulty {dif}"
        self.command_send(command)

    def server_list(self):
        server_folder_path = os.path.expanduser(f"~/Documents/Minecraft_server")
        server_list_name = [f for f in os.listdir(server_folder_path)
                            if os.path.isdir(os.path.join(server_folder_path, f)) and f != "jdk"]

        server_version_list = []
        for parent_folder in server_list_name:
            parent_path = os.path.join(server_folder_path, parent_folder)
            for sub1 in os.listdir(parent_path):
                sub1_path = os.path.join(parent_path, sub1)
                if os.path.isdir(sub1_path):
                    for sub2 in os.listdir(sub1_path):
                        sub2_path = os.path.join(sub1_path, sub2)
                        if os.path.isdir(sub2_path):
                            server_version_list.append(os.path.join(parent_folder, sub1, sub2))

        return server_version_list

    def nogui_toggle(self, onoff, name, win):
        server_folder_path = f"{os.path.expanduser(f"~/Documents/Minecraft_server")}/{name}"
        if not win:
            run_sh_path = os.path.join(server_folder_path, "run.sh")
        else:
            run_sh_path = os.path.join(server_folder_path, "run.bat")
        # 파일 내용 읽기
        with open(run_sh_path, "r") as file:
            lines = file.readlines()

        # 수정된 라인 저장
        new_lines = []

        if onoff:
            for line in lines:
                if "server.jar" in line and "nogui" not in line:
                    if not win and '"$@"' in line:
                        line = line.replace('"$@"', 'nogui "$@"')
                    elif win and '%*' in line:
                        # 앞뒤 공백 정리하며 대체
                        line = re.sub(r'\s*%[*]', ' nogui %*', line)
                    else:
                        line = line.strip() + " nogui\n"
                new_lines.append(line)

            # 파일 덮어쓰기
            with open(run_sh_path, "w") as file:
                file.writelines(new_lines)
        else:
            for line in lines:
                if "server.jar" in line and "nogui" in line:
                    line = line.replace("nogui", "").replace("  ", " ").strip() + "\n"
                new_lines.append(line)

            # 파일 덮어쓰기
            with open(run_sh_path, "w") as file:
                file.writelines(new_lines)
