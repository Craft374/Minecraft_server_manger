import customtkinter as ctk
import webbrowser
import time
import requests
from requests.exceptions import ChunkedEncodingError
from urllib.parse import urlsplit
import shutil
import tarfile
import sys
import os
import json
from sub_process import ServerFunctions

class Server_create:
    def __init__(self, app):
        self.app = app  # ServerManagerApp 인스턴스를 받아 저장
        self.version_data = {}
        self.selected_version = ctk.StringVar()
        self.selected_subversion = ctk.StringVar()

        self.sub = ServerFunctions(self)

    def tab_paper(self):
        self.tabview.add("paper")
        tab = self.tabview.tab("paper")

    def tab_forge(self):
        self.tabview.add("forge")
        # self.tabview.grid(row=0, column=0, sticky="nsew")
        tab = self.tabview.tab("forge")
        # tab.grid_rowconfigure((0, 1, 2), weight=1)
        # tab.grid_columnconfigure(0, weight=1)

        forge_version_url = "https://gist.githubusercontent.com/Craft374/06ac4b5be32e38efa0fee9923313eabe/raw/forge-version.json"
        self.version_data = requests.get(forge_version_url).json()

        version_list = list(self.version_data.keys())
        if not version_list:
            return

        # 첫 번째 드롭박스 (버전)
        self.version_dropdown = ctk.CTkOptionMenu(tab, variable=self.selected_version, values=version_list,
                                             command=self.update_subversion)
        self.version_dropdown.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=5, pady=5)
        self.version_dropdown.set(version_list[0])

        # 두 번째 드롭박스 (세부 버전)
        self.subversion_dropdown = ctk.CTkOptionMenu(tab, variable=self.selected_subversion, values=[])
        self.subversion_dropdown.grid(row=1, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=5, pady=5)
        self.version_dropdown.set(version_list[0])
        self.update_subversion(version_list[0])

        self.download_button = ctk.CTkButton(tab, text="다운로드", command=lambda: self.sub.download_installer(
    self.version_data[self.selected_version.get()]["versions"][self.selected_subversion.get()]))
        self.download_button.grid(row=2, column=0, rowspan=1, columnspan=1, sticky="nsew", padx=5, pady=5)

    def tab_fabric(self):
        self.tabview.add("fabric")
        tab = self.tabview.tab("fabric")

        # JSON 데이터 로드 (forge와 같은 구조 가정)
        fabric_version_url = "https://gist.githubusercontent.com/Craft374/06ac4b5be32e38efa0fee9923313eabe/raw/forge-version.json"
        response = requests.get(fabric_version_url)
        if response.status_code != 200:
            print("요청 실패:", response.status_code)
            return
        try:
            self.fabric_data = response.json()
        except json.JSONDecodeError:
            print("JSON 디코드 실패")
            return

        # 프레임 나누기
        left_frame = ctk.CTkScrollableFrame(tab, width=200)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)

        right_frame = ctk.CTkScrollableFrame(tab)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        self.right_frame = right_frame  # 나중에 업데이트용으로 저장

        # 좌측 메인 버전 버튼들 생성
        for main_ver in self.fabric_data.keys():
            btn = ctk.CTkButton(left_frame, text=main_ver,
                                command=lambda v=main_ver: self.populate_subversions(v))
            btn.pack(fill="x", pady=2)

    def populate_subversions(self, main_ver):
        # 기존 버튼들 제거
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        subversions = self.fabric_data[main_ver]["versions"]
        for sub_ver, url in subversions.items():
            btn = ctk.CTkButton(self.right_frame, text=sub_ver,
                                command=lambda u=url: self.sub.download_installer(u))
            btn.pack(fill="x", pady=2)

    def open_create_window(self):
        self.create_window = ctk.CTkToplevel(self.app)
        self.create_window.title("서버 제작")
        self.create_window.geometry("850x510+75+100")
        self.create_window.grab_set()

        self.tabview = ctk.CTkTabview(self.create_window)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.tab_paper()
        self.tab_forge()
        self.tab_fabric()

    def update_subversion(self, selected_version):
        subversions = list(self.version_data[selected_version]["versions"].keys())
        if subversions:
            self.selected_subversion.set(subversions[0])
            self.subversion_dropdown.configure(values=subversions)
        else:
            self.selected_subversion.set("")
            self.subversion_dropdown.configure(values=[])