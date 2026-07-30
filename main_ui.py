import os
import platform
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from server_core import (
    APP_VERSION,
    ConfigStore,
    JdkManager,
    build_launch_command,
    detect_minecraft_version,
    find_launch_target,
    java_feature_for_minecraft,
)


FONT = "Noto Sans KR"
BG_COLOR = ("#F2F5F1", "#0D1210")
SIDEBAR_COLOR = ("#E7ECE6", "#121A16")
PANEL_COLOR = ("#FFFFFF", "#18231D")
PANEL_HOVER = ("#DDE6DC", "#213026")
ACCENT_COLOR = "#7FC96A"
ACCENT_HOVER = "#69B157"
ACCENT_TEXT = "#102010"
TEXT_COLOR = ("#18201B", "#F3F7F2")
MUTED_TEXT = ("#66736A", "#93A399")
LINE_COLOR = ("#CDD7CE", "#2A3A30")
DANGER_COLOR = "#D85F5F"
DANGER_HOVER = "#B94B4B"
WARNING_COLOR = "#E6B85C"


class ServerManagerApp(ctk.CTk):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.store.discover_legacy_servers()

        self.selected_server = None
        self.active_server_path = None
        self.server_process = None
        self.server_buttons = []
        self.operation_in_progress = False

        self.title(f"EMSR v{APP_VERSION}")
        self.geometry("1180x760")
        self.minsize(1040, 680)
        self.configure(fg_color=BG_COLOR)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_content()
        self.refresh_server_list()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=286,
            corner_radius=0,
            fg_color=SIDEBAR_COLOR,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(25, 19))

        ctk.CTkLabel(
            brand,
            text="EMSR",
            font=ctk.CTkFont(family=FONT, size=30, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text=f"Easy Minecraft Server Runner  ·  v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT, size=11),
            text_color=MUTED_TEXT,
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkLabel(
            sidebar,
            text="내 서버",
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            text_color=MUTED_TEXT,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 8))

        self.server_list_frame = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=LINE_COLOR,
            scrollbar_button_hover_color=PANEL_HOVER,
        )
        self.server_list_frame.grid(row=2, column=0, sticky="nsew", padx=13)
        self.server_list_frame.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(
            sidebar,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=LINE_COLOR,
        )
        actions.grid(row=3, column=0, sticky="ew", padx=16, pady=16)
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions,
            text="서버 불러오기",
            height=42,
            corner_radius=12,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            command=self.open_import_dialog,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=11, pady=(11, 7))

        ctk.CTkButton(
            actions,
            text="＋ 서버 제작",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family=FONT, size=12),
            command=self.show_create_server_notice,
        ).grid(row=1, column=0, sticky="ew", padx=(11, 4), pady=(0, 11))

        ctk.CTkButton(
            actions,
            text="설정",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family=FONT, size=12),
            command=self.open_settings_dialog,
        ).grid(row=1, column=1, sticky="ew", padx=(4, 11), pady=(0, 11))

    def _build_main_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            content,
            fg_color=PANEL_COLOR,
            corner_radius=20,
            border_width=1,
            border_color=LINE_COLOR,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        header_text = ctk.CTkFrame(header, fg_color="transparent")
        header_text.grid(row=0, column=0, sticky="ew", padx=22, pady=18)

        self.selected_name_label = ctk.CTkLabel(
            header_text,
            text="서버를 선택해 주세요",
            font=ctk.CTkFont(family=FONT, size=23, weight="bold"),
            text_color=TEXT_COLOR,
            anchor="w",
        )
        self.selected_name_label.pack(anchor="w")

        self.selected_path_label = ctk.CTkLabel(
            header_text,
            text="왼쪽에서 기존 서버를 불러올 수 있습니다.",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=MUTED_TEXT,
            anchor="w",
        )
        self.selected_path_label.pack(anchor="w", pady=(5, 0))

        self.open_folder_button = ctk.CTkButton(
            header,
            text="폴더 열기",
            width=94,
            height=42,
            corner_radius=12,
            fg_color="transparent",
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            state="disabled",
            command=self.open_selected_folder,
        )
        self.open_folder_button.grid(row=0, column=1, padx=(8, 0), pady=18)

        self.start_button = ctk.CTkButton(
            header,
            text="서버 시작",
            width=120,
            height=42,
            corner_radius=12,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
            state="disabled",
            command=self.toggle_server,
        )
        self.start_button.grid(row=0, column=2, padx=(10, 18), pady=18)

        self.tabview = ctk.CTkTabview(
            content,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            segmented_button_fg_color=PANEL_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_hover_color=PANEL_HOVER,
            text_color=TEXT_COLOR,
            anchor="nw",
        )
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.tabview.add("대시보드")
        self.tabview.add("콘솔")
        self.tabview.add("빠른 명령")

        self._build_dashboard_tab()
        self._build_console_tab()
        self._build_commands_tab()

    def _build_dashboard_tab(self):
        tab = self.tabview.tab("대시보드")
        tab.configure(fg_color=BG_COLOR)
        tab.grid_columnconfigure((0, 1, 2), weight=1, uniform="metric")
        tab.grid_rowconfigure(1, weight=1)

        self.status_value = self._make_metric_card(
            tab,
            0,
            "서버 상태",
            "선택 안 됨",
            "서버 프로세스 상태",
        )
        self.version_value = self._make_metric_card(
            tab,
            1,
            "Minecraft",
            "-",
            "불러올 때 확인한 버전",
        )
        self.java_value = self._make_metric_card(
            tab,
            2,
            "Java",
            "-",
            "필요한 JDK 자동 관리",
        )

        guide = ctk.CTkFrame(
            tab,
            fg_color=PANEL_COLOR,
            corner_radius=22,
            border_width=1,
            border_color=LINE_COLOR,
        )
        guide.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=4,
            pady=(14, 4),
        )
        guide.grid_columnconfigure(0, weight=1)
        guide.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            guide,
            text="기존 서버를 그대로 연결합니다",
            font=ctk.CTkFont(family=FONT, size=21, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 7))

        ctk.CTkLabel(
            guide,
            text=(
                "서버 폴더와 Minecraft 버전을 등록하면 필요한 Java 버전을 계산합니다.\n"
                "설정한 JDK 경로에 Java가 없을 경우 서버 시작 시 자동 설치한 뒤 바로 실행합니다."
            ),
            font=ctk.CTkFont(family=FONT, size=13),
            text_color=MUTED_TEXT,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24)

        flow = ctk.CTkFrame(guide, fg_color="transparent")
        flow.grid(row=2, column=0, sticky="nsew", padx=24, pady=22)
        flow.grid_columnconfigure((0, 1, 2), weight=1, uniform="flow")

        steps = (
            ("1", "서버 불러오기", "run.bat, run.sh 또는 서버 JAR 확인"),
            ("2", "Java 준비", "버전에 맞는 JDK 확인 및 자동 설치"),
            ("3", "서버 실행", "같은 화면에서 로그와 명령 관리"),
        )
        for column, (number, title, description) in enumerate(steps):
            card = ctk.CTkFrame(
                flow,
                fg_color=SIDEBAR_COLOR,
                corner_radius=17,
                border_width=1,
                border_color=LINE_COLOR,
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 6, 0 if column == 2 else 6),
            )
            ctk.CTkLabel(
                card,
                text=number,
                width=34,
                height=34,
                corner_radius=17,
                fg_color=ACCENT_COLOR,
                text_color=ACCENT_TEXT,
                font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            ).pack(anchor="w", padx=17, pady=(17, 12))
            ctk.CTkLabel(
                card,
                text=title,
                text_color=TEXT_COLOR,
                font=ctk.CTkFont(family=FONT, size=15, weight="bold"),
            ).pack(anchor="w", padx=17)
            ctk.CTkLabel(
                card,
                text=description,
                wraplength=190,
                justify="left",
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(family=FONT, size=11),
            ).pack(anchor="w", padx=17, pady=(6, 17))

    def _make_metric_card(self, parent, column, title, value, description):
        card = ctk.CTkFrame(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=LINE_COLOR,
        )
        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(4 if column == 0 else 7, 4 if column == 2 else 7),
            pady=4,
        )

        ctk.CTkLabel(
            card,
            text=title,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(17, 5))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family=FONT, size=19, weight="bold"),
        )
        value_label.pack(anchor="w", padx=18)

        ctk.CTkLabel(
            card,
            text=description,
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=10),
        ).pack(anchor="w", padx=18, pady=(5, 17))
        return value_label

    def _build_console_tab(self):
        tab = self.tabview.tab("콘솔")
        tab.configure(fg_color=BG_COLOR)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        console_card = ctk.CTkFrame(
            tab,
            fg_color=PANEL_COLOR,
            corner_radius=20,
            border_width=1,
            border_color=LINE_COLOR,
        )
        console_card.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        console_card.grid_columnconfigure(0, weight=1)
        console_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            console_card,
            text="서버 콘솔",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family=FONT, size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        self.log_text = ctk.CTkTextbox(
            console_card,
            fg_color="#0B100D",
            text_color="#D9E4DB",
            border_width=1,
            border_color=LINE_COLOR,
            corner_radius=12,
            font=("Menlo", 12),
            state="disabled",
        )
        self.log_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=16)

        self.command_entry = ctk.CTkEntry(
            console_card,
            height=44,
            corner_radius=12,
            fg_color=SIDEBAR_COLOR,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="명령어 입력 후 Enter",
            font=ctk.CTkFont(family=FONT, size=13),
        )
        self.command_entry.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(16, 8),
            pady=16,
        )
        self.command_entry.bind("<Return>", self._send_entry_command)

        ctk.CTkButton(
            console_card,
            text="전송",
            width=82,
            height=44,
            corner_radius=12,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
            command=self._send_entry_command,
        ).grid(row=2, column=1, padx=(0, 16), pady=16)

    def _build_commands_tab(self):
        tab = self.tabview.tab("빠른 명령")
        tab.configure(fg_color=BG_COLOR)
        tab.grid_columnconfigure((0, 1), weight=1, uniform="command")
        tab.grid_rowconfigure(0, weight=1)

        player_card = self._make_command_card(tab, 0, "플레이어 관리")
        self.player_entry = ctk.CTkEntry(
            player_card,
            height=42,
            placeholder_text="플레이어 이름",
            fg_color=SIDEBAR_COLOR,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
        )
        self.player_entry.pack(fill="x", padx=18, pady=(0, 12))

        player_buttons = ctk.CTkFrame(player_card, fg_color="transparent")
        player_buttons.pack(fill="x", padx=13)
        for index, command in enumerate(("kick", "ban", "pardon", "op", "deop")):
            button = ctk.CTkButton(
                player_buttons,
                text=command,
                height=36,
                corner_radius=10,
                fg_color=PANEL_HOVER,
                hover_color=LINE_COLOR,
                text_color=TEXT_COLOR,
                command=lambda value=command: self.send_player_command(value),
            )
            button.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=5,
                pady=5,
            )
        player_buttons.grid_columnconfigure((0, 1, 2), weight=1)

        mode_frame = ctk.CTkFrame(player_card, fg_color="transparent")
        mode_frame.pack(fill="x", padx=18, pady=(15, 18))
        mode_frame.grid_columnconfigure(0, weight=1)
        self.gamemode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=("survival", "creative", "adventure", "spectator"),
            height=39,
            fg_color=PANEL_HOVER,
            button_color=LINE_COLOR,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_COLOR,
        )
        self.gamemode_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(
            mode_frame,
            text="게임모드 변경",
            width=110,
            height=39,
            corner_radius=10,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            command=self.send_gamemode_command,
        ).grid(row=0, column=1)

        world_card = self._make_command_card(tab, 1, "월드 관리")
        commands = (
            ("낮으로 변경", "time set day"),
            ("밤으로 변경", "time set night"),
            ("맑은 날씨", "weather clear"),
            ("비 오는 날씨", "weather rain"),
            ("평화로움", "difficulty peaceful"),
            ("보통 난이도", "difficulty normal"),
            ("월드 저장", "save-all"),
            ("서버 정보", "list"),
        )
        world_buttons = ctk.CTkFrame(world_card, fg_color="transparent")
        world_buttons.pack(fill="both", expand=True, padx=13, pady=(0, 18))
        world_buttons.grid_columnconfigure((0, 1), weight=1)
        for index, (label, command) in enumerate(commands):
            ctk.CTkButton(
                world_buttons,
                text=label,
                height=42,
                corner_radius=11,
                fg_color=PANEL_HOVER,
                hover_color=LINE_COLOR,
                text_color=TEXT_COLOR,
                command=lambda value=command: self.send_command(value),
            ).grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=5,
                pady=5,
            )

    def _make_command_card(self, parent, column, title):
        card = ctk.CTkFrame(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=20,
            border_width=1,
            border_color=LINE_COLOR,
        )
        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(4 if column == 0 else 8, 4 if column == 1 else 8),
            pady=4,
        )
        ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family=FONT, size=17, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 15))
        return card

    def refresh_server_list(self, select_path=None):
        for widget in self.server_list_frame.winfo_children():
            widget.destroy()
        self.server_buttons = []

        servers = self.store.data.get("servers", [])
        if not servers:
            ctk.CTkLabel(
                self.server_list_frame,
                text="불러온 서버가 없습니다.\n아래 버튼으로 서버 폴더를 연결해 주세요.",
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(family=FONT, size=12),
                justify="left",
            ).grid(row=0, column=0, sticky="w", padx=9, pady=10)
            self.select_server(None)
            return

        for row, server in enumerate(servers):
            version = server.get("minecraft_version") or "버전 미확인"
            path_exists = Path(server.get("path", "")).is_dir()
            suffix = "" if path_exists else " · 경로 없음"
            button = ctk.CTkButton(
                self.server_list_frame,
                text=f"{server.get('name', '이름 없는 서버')}\n{version}{suffix}",
                height=58,
                corner_radius=13,
                anchor="w",
                fg_color="transparent",
                hover_color=PANEL_HOVER,
                border_width=1,
                border_color=LINE_COLOR,
                text_color=TEXT_COLOR if path_exists else MUTED_TEXT,
                font=ctk.CTkFont(family=FONT, size=12),
                command=lambda value=server: self.select_server(value),
            )
            button.grid(row=row, column=0, sticky="ew", padx=1, pady=4)
            self.server_buttons.append((server, button))

        target = None
        if select_path:
            target = next(
                (
                    server
                    for server in servers
                    if server.get("path") == str(Path(select_path).resolve())
                ),
                None,
            )
        self.select_server(target or servers[0])

    def select_server(self, server):
        self.selected_server = server
        for value, button in self.server_buttons:
            selected = server and value.get("path") == server.get("path")
            button.configure(
                fg_color=PANEL_HOVER if selected else "transparent",
                border_color=ACCENT_COLOR if selected else LINE_COLOR,
            )

        if not server:
            self.selected_name_label.configure(text="서버를 선택해 주세요")
            self.selected_path_label.configure(
                text="왼쪽에서 기존 서버를 불러올 수 있습니다."
            )
            self.start_button.configure(state="disabled", text="서버 시작")
            self.open_folder_button.configure(state="disabled")
            self.status_value.configure(text="선택 안 됨", text_color=MUTED_TEXT)
            self.version_value.configure(text="-")
            self.java_value.configure(text="-")
            return

        server_path = Path(server.get("path", ""))
        self.selected_name_label.configure(text=server.get("name", server_path.name))
        self.selected_path_label.configure(text=str(server_path))
        self.open_folder_button.configure(
            state="normal" if server_path.is_dir() else "disabled"
        )
        self.start_button.configure(
            state="normal" if server_path.is_dir() else "disabled"
        )
        self._update_dashboard()

    def _update_dashboard(self):
        if not self.selected_server:
            return

        server_path = Path(self.selected_server.get("path", ""))
        minecraft_version = self.selected_server.get("minecraft_version") or "자동 감지"
        java_version = java_feature_for_minecraft(minecraft_version)
        java_path = JdkManager(self.store.data["jdk_path"]).find_java(java_version)

        self.version_value.configure(text=minecraft_version)
        if java_path:
            self.java_value.configure(
                text=f"Java {java_version} 준비됨",
                text_color=ACCENT_COLOR,
            )
        else:
            self.java_value.configure(
                text=f"Java {java_version} 설치 필요",
                text_color=WARNING_COLOR,
            )

        process_running = (
            self.server_process is not None
            and self.server_process.poll() is None
            and self.active_server_path == str(server_path)
        )
        if process_running:
            self.status_value.configure(text="실행 중", text_color=ACCENT_COLOR)
            self.start_button.configure(
                text="서버 정지",
                fg_color=DANGER_COLOR,
                hover_color=DANGER_HOVER,
                text_color=TEXT_COLOR,
            )
        elif not server_path.is_dir():
            self.status_value.configure(text="경로 없음", text_color=DANGER_COLOR)
            self.start_button.configure(state="disabled")
        else:
            self.status_value.configure(text="실행 준비", text_color=TEXT_COLOR)
            self.start_button.configure(
                text="서버 시작",
                state="normal",
                fg_color=ACCENT_COLOR,
                hover_color=ACCENT_HOVER,
                text_color=ACCENT_TEXT,
            )

    def open_import_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("기존 서버 불러오기")
        dialog.geometry("640x405")
        dialog.resizable(False, False)
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="기존 서버 불러오기",
            font=ctk.CTkFont(family=FONT, size=23, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=26, pady=(24, 5))
        ctk.CTkLabel(
            dialog,
            text="서버 폴더 안의 실행 스크립트 또는 서버 JAR을 확인합니다.",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=MUTED_TEXT,
        ).grid(row=1, column=0, sticky="w", padx=26, pady=(0, 17))

        form = ctk.CTkFrame(
            dialog,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=LINE_COLOR,
        )
        form.grid(row=2, column=0, sticky="ew", padx=26)
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form,
            text="서버 폴더 경로",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(15, 5))

        path_entry = ctk.CTkEntry(
            form,
            height=42,
            fg_color=SIDEBAR_COLOR,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="예: C:\\Minecraft\\MyServer 또는 /Users/me/Minecraft/MyServer",
        )
        path_entry.grid(row=1, column=0, sticky="ew", padx=(16, 7))

        name_entry = ctk.CTkEntry(
            form,
            height=42,
            fg_color=SIDEBAR_COLOR,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="목록에 표시할 서버 이름",
        )
        version_entry = ctk.CTkEntry(
            form,
            height=42,
            fg_color=SIDEBAR_COLOR,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="Minecraft 버전 예: 1.21.1",
        )

        def fill_from_path():
            raw_path = path_entry.get().strip()
            if not raw_path:
                return
            server_path = Path(raw_path).expanduser()
            if not name_entry.get().strip():
                name_entry.insert(0, server_path.name)
            if not version_entry.get().strip() and server_path.is_dir():
                detected = detect_minecraft_version(server_path)
                if detected:
                    version_entry.insert(0, detected)

        def browse_folder():
            selected = filedialog.askdirectory(
                parent=dialog,
                title="기존 Minecraft 서버 폴더 선택",
            )
            if not selected:
                return
            path_entry.delete(0, "end")
            path_entry.insert(0, selected)
            fill_from_path()

        ctk.CTkButton(
            form,
            text="찾아보기",
            width=86,
            height=42,
            fg_color=PANEL_HOVER,
            hover_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            command=browse_folder,
        ).grid(row=1, column=1, padx=(0, 16))

        ctk.CTkLabel(
            form,
            text="서버 이름",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(13, 5))
        name_entry.grid(row=3, column=0, sticky="ew", padx=(16, 7), pady=(0, 15))

        ctk.CTkLabel(
            form,
            text="Minecraft 버전",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(13, 5))
        version_entry.grid(row=3, column=1, sticky="ew", padx=(0, 16), pady=(0, 15))

        def import_server():
            raw_path = path_entry.get().strip()
            if not raw_path:
                messagebox.showwarning("경로 확인", "서버 폴더 경로를 입력해 주세요.", parent=dialog)
                return

            server_path = Path(raw_path).expanduser()
            if not server_path.is_dir():
                messagebox.showerror("경로 오류", "입력한 서버 폴더를 찾을 수 없습니다.", parent=dialog)
                return
            if not find_launch_target(server_path):
                messagebox.showerror(
                    "서버 파일 없음",
                    "현재 운영체제용 run 파일 또는 실행 가능한 서버 JAR을 찾지 못했습니다.",
                    parent=dialog,
                )
                return

            minecraft_version = (
                version_entry.get().strip() or detect_minecraft_version(server_path)
            )
            if not minecraft_version:
                messagebox.showwarning(
                    "버전 확인",
                    "필요한 Java 버전을 판단할 수 있도록 Minecraft 버전을 입력해 주세요.",
                    parent=dialog,
                )
                return

            entry = self.store.add_server(
                name_entry.get().strip() or server_path.name,
                server_path,
                minecraft_version,
            )
            dialog.destroy()
            self.refresh_server_list(entry["path"])
            messagebox.showinfo(
                "불러오기 완료",
                "서버를 불러왔습니다.\n서버 시작을 누르면 필요한 Java를 자동으로 준비합니다.",
                parent=self,
            )

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="e", padx=26, pady=20)
        ctk.CTkButton(
            buttons,
            text="취소",
            width=90,
            height=40,
            fg_color="transparent",
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            command=dialog.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="불러오기",
            width=100,
            height=40,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            command=import_server,
        ).pack(side="left")

    def open_settings_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("설정")
        dialog.geometry("620x430")
        dialog.resizable(False, False)
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="설정",
            font=ctk.CTkFont(family=FONT, size=23, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=26, pady=(24, 5))
        ctk.CTkLabel(
            dialog,
            text="JDK 설치 위치와 화면 표시 방식을 저장합니다.",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=MUTED_TEXT,
        ).grid(row=1, column=0, sticky="w", padx=26, pady=(0, 17))

        form = ctk.CTkFrame(
            dialog,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=LINE_COLOR,
        )
        form.grid(row=2, column=0, sticky="ew", padx=26)
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form,
            text="JDK 설치 위치",
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 3))
        ctk.CTkLabel(
            form,
            text="서버 버전별 Java가 이 폴더 아래에 설치됩니다.",
            font=ctk.CTkFont(family=FONT, size=10),
            text_color=MUTED_TEXT,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        jdk_entry = ctk.CTkEntry(
            form,
            height=42,
            fg_color=SIDEBAR_COLOR,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
        )
        jdk_entry.insert(0, self.store.data["jdk_path"])
        jdk_entry.grid(row=2, column=0, sticky="ew", padx=(16, 7))

        def browse_jdk_folder():
            selected = filedialog.askdirectory(
                parent=dialog,
                title="JDK를 설치할 폴더 선택",
            )
            if selected:
                jdk_entry.delete(0, "end")
                jdk_entry.insert(0, selected)

        ctk.CTkButton(
            form,
            text="찾아보기",
            width=86,
            height=42,
            fg_color=PANEL_HOVER,
            hover_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            command=browse_jdk_folder,
        ).grid(row=2, column=1, padx=(0, 16))

        appearance = ctk.CTkFrame(form, fg_color="transparent")
        appearance.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=17)
        appearance.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            appearance,
            text="테마",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ctk.CTkLabel(
            appearance,
            text="UI 크기",
            text_color=MUTED_TEXT,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 5))

        theme_menu = ctk.CTkOptionMenu(
            appearance,
            values=("Dark", "Light", "System"),
            height=40,
            fg_color=PANEL_HOVER,
            button_color=LINE_COLOR,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_COLOR,
        )
        theme_menu.set(self.store.data.get("theme", "Dark"))
        theme_menu.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        scale_menu = ctk.CTkOptionMenu(
            appearance,
            values=("80%", "90%", "100%", "110%", "120%"),
            height=40,
            fg_color=PANEL_HOVER,
            button_color=LINE_COLOR,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_COLOR,
        )
        scale_menu.set(self.store.data.get("ui_scale", "100%"))
        scale_menu.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        def save_settings():
            jdk_path = jdk_entry.get().strip()
            if not jdk_path:
                messagebox.showwarning(
                    "경로 확인",
                    "JDK 설치 위치를 입력해 주세요.",
                    parent=dialog,
                )
                return

            self.store.data["jdk_path"] = str(Path(jdk_path).expanduser())
            self.store.data["theme"] = theme_menu.get()
            self.store.data["ui_scale"] = scale_menu.get()
            self.store.save()
            ctk.set_appearance_mode(theme_menu.get())
            ctk.set_widget_scaling(int(scale_menu.get().replace("%", "")) / 100)
            dialog.destroy()
            self._update_dashboard()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="e", padx=26, pady=20)
        ctk.CTkButton(
            buttons,
            text="취소",
            width=90,
            height=40,
            fg_color="transparent",
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=LINE_COLOR,
            text_color=TEXT_COLOR,
            command=dialog.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons,
            text="저장",
            width=90,
            height=40,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=ACCENT_TEXT,
            command=save_settings,
        ).pack(side="left")

    def show_create_server_notice(self):
        messagebox.showinfo(
            "서버 제작",
            "서버 제작 기능은 다음 업데이트에서 제공할 예정입니다.",
            parent=self,
        )

    def open_selected_folder(self):
        if not self.selected_server:
            return
        server_path = Path(self.selected_server["path"])
        if not server_path.is_dir():
            messagebox.showerror("경로 오류", "서버 폴더를 찾을 수 없습니다.", parent=self)
            return

        if platform.system() == "Windows":
            os.startfile(str(server_path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(server_path)])
        else:
            messagebox.showerror(
                "지원하지 않는 운영체제",
                "폴더 열기는 Windows와 macOS만 지원합니다.",
                parent=self,
            )

    def toggle_server(self):
        if self.server_process and self.server_process.poll() is None:
            if (
                self.selected_server
                and self.active_server_path == self.selected_server.get("path")
            ):
                self.stop_server()
            else:
                messagebox.showwarning(
                    "서버 실행 중",
                    "다른 서버가 실행 중입니다. 먼저 해당 서버를 종료해 주세요.",
                    parent=self,
                )
            return

        if not self.selected_server or self.operation_in_progress:
            return

        server_path = Path(self.selected_server["path"])
        if not server_path.is_dir():
            messagebox.showerror("경로 오류", "서버 폴더를 찾을 수 없습니다.", parent=self)
            return

        self.operation_in_progress = True
        self.start_button.configure(state="disabled", text="Java 확인 중")
        self.status_value.configure(text="준비 중", text_color=WARNING_COLOR)
        self.tabview.set("콘솔")
        self.append_log("[EMSR] 서버 실행을 준비합니다.\n")
        threading.Thread(
            target=self._prepare_and_start_server,
            args=(self.selected_server.copy(),),
            daemon=True,
        ).start()

    def _prepare_and_start_server(self, server):
        try:
            minecraft_version = server.get("minecraft_version", "")
            java_version = java_feature_for_minecraft(minecraft_version)
            jdk_manager = JdkManager(self.store.data["jdk_path"])
            java_path = jdk_manager.find_java(java_version)

            if not java_path:
                self._queue_log(
                    f"[EMSR] Java {java_version}이 없어 설정 경로에 설치합니다.\n"
                )
                java_path = jdk_manager.install(
                    java_version,
                    progress_callback=self._queue_install_status,
                )

            server_path = Path(server["path"])
            command = build_launch_command(server_path, java_path)
            environment = os.environ.copy()
            java_home = jdk_manager.java_home(java_path)
            environment["JAVA_HOME"] = str(java_home)
            environment["PATH"] = (
                str(java_home / "bin")
                + os.pathsep
                + environment.get("PATH", "")
            )

            popen_options = {
                "cwd": str(server_path),
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
                "bufsize": 1,
                "env": environment,
            }
            if platform.system() == "Windows":
                popen_options["creationflags"] = getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0,
                )

            self._queue_log(
                f"[EMSR] Java {java_version} 준비 완료: {java_path}\n"
            )
            process = subprocess.Popen(command, **popen_options)
            self.server_process = process
            self.active_server_path = server["path"]
            self.after(0, self._on_process_started, server)

            if process.stdout:
                for line in process.stdout:
                    self._queue_log(line)

            exit_code = process.wait()
            self.after(0, self._on_process_exited, process, exit_code)
        except Exception as error:
            self.after(0, self._on_start_failed, str(error))

    def _queue_install_status(self, text):
        self.after(
            0,
            lambda: self.start_button.configure(text="Java 설치 중"),
        )
        self.after(
            0,
            lambda: self.status_value.configure(
                text=text,
                text_color=WARNING_COLOR,
            ),
        )
        self._queue_log(f"[EMSR] {text}\n")

    def _queue_log(self, text):
        self.after(0, self.append_log, text)

    def _on_process_started(self, server):
        self.operation_in_progress = False
        self._update_dashboard()
        self.append_log(f"[EMSR] {server['name']} 서버를 시작했습니다.\n")

    def _on_process_exited(self, process, exit_code):
        if self.server_process is not process:
            return
        self.server_process = None
        self.active_server_path = None
        self.operation_in_progress = False
        self.append_log(f"[EMSR] 서버가 종료되었습니다. 종료 코드: {exit_code}\n")
        self._update_dashboard()

    def _on_start_failed(self, error_message):
        self.server_process = None
        self.active_server_path = None
        self.operation_in_progress = False
        self.append_log(f"[EMSR] 서버 시작 실패: {error_message}\n")
        self._update_dashboard()
        messagebox.showerror(
            "서버 시작 실패",
            error_message,
            parent=self,
        )

    def stop_server(self, close_after=False):
        process = self.server_process
        if not process or process.poll() is not None:
            if close_after:
                self.destroy()
            return

        self.operation_in_progress = True
        self.start_button.configure(state="disabled", text="종료 중")
        self.status_value.configure(text="종료 중", text_color=WARNING_COLOR)
        self.append_log("[EMSR] 서버를 안전하게 종료합니다.\n")

        def stop_worker():
            try:
                for command in ("save-all", "stop"):
                    try:
                        self._write_process_command(command)
                    except (OSError, RuntimeError) as error:
                        self._queue_log(
                            f"[EMSR] {command} 명령 전송 실패: {error}\n"
                        )
                try:
                    process.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
            finally:
                if close_after:
                    self.after(0, self.destroy)

        threading.Thread(target=stop_worker, daemon=True).start()

    def _write_process_command(self, command):
        process = self.server_process
        if not process or process.poll() is not None or not process.stdin:
            raise RuntimeError("실행 중인 서버 콘솔에 연결되어 있지 않습니다.")
        process.stdin.write(command.strip() + "\n")
        process.stdin.flush()

    def send_command(self, command):
        command = command.strip()
        if not command:
            return
        try:
            self._write_process_command(command)
            self.append_log(f"> {command}\n")
        except (OSError, RuntimeError) as error:
            self.append_log(f"[EMSR] 명령 전송 실패: {error}\n")

    def _send_entry_command(self, _event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        self.send_command(command)
        self.command_entry.delete(0, "end")

    def send_player_command(self, command):
        player = self.player_entry.get().strip()
        if not player:
            messagebox.showwarning(
                "플레이어 이름",
                "플레이어 이름을 입력해 주세요.",
                parent=self,
            )
            return
        self.send_command(f"{command} {player}")

    def send_gamemode_command(self):
        player = self.player_entry.get().strip()
        if not player:
            messagebox.showwarning(
                "플레이어 이름",
                "플레이어 이름을 입력해 주세요.",
                parent=self,
            )
            return
        self.send_command(f"gamemode {self.gamemode_menu.get()} {player}")

    def append_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def on_close(self):
        if self.operation_in_progress and not (
            self.server_process and self.server_process.poll() is None
        ):
            messagebox.showinfo(
                "작업 진행 중",
                "Java 설치 또는 서버 시작 준비가 끝난 뒤 종료해 주세요.",
                parent=self,
            )
            return

        if self.server_process and self.server_process.poll() is None:
            should_stop = messagebox.askyesno(
                "서버 종료",
                "서버를 안전하게 종료한 뒤 EMSR을 닫을까요?",
                parent=self,
            )
            if should_stop:
                self.stop_server(close_after=True)
            return
        self.destroy()


def run_app():
    store = ConfigStore()
    ctk.set_appearance_mode(store.data.get("theme", "Dark"))
    ctk.set_default_color_theme("blue")
    scale = store.data.get("ui_scale", "100%")
    ctk.set_widget_scaling(int(scale.replace("%", "")) / 100)
    app = ServerManagerApp(store)
    app.mainloop()


if __name__ == "__main__":
    if platform.system() not in ("Windows", "Darwin"):
        print("EMSR은 Windows와 macOS를 지원합니다.")
        sys.exit(1)
    run_app()
