import json
import os
import re
import threading
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

import customtkinter as ctk
import requests


FONT = "Noto Sans KR"
ARCHIVE_ROOT = Path(__file__).resolve().parent
DATA_ROOT = ARCHIVE_ROOT / "data"
DOWNLOAD_ROOT = ARCHIVE_ROOT / "downloads"
FORGE_METADATA_URL = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
FORGE_BASE_URL = "https://maven.minecraftforge.net/net/minecraftforge/forge"

BG_COLOR = "#0F1411"
PANEL_COLOR = "#18211B"
PANEL_ALT_COLOR = "#223126"
ACCENT_COLOR = "#83C26B"
ACCENT_HOVER = "#6EA75A"
TEXT_COLOR = "#F4F7F1"
MUTED_TEXT = "#9FB29F"
WARN_COLOR = "#E8C26E"


class ServerCreateWindow:
    def __init__(self, app):
        self.app = app
        self.create_window = None

        self.forge_versions = {}
        self.forge_selected_mc = ""
        self.forge_selected_build = ""

        self.paper_versions = self._read_lines(DATA_ROOT / "paper_versions.txt")
        self.fabric_versions = self._read_lines(DATA_ROOT / "fabric_versions.txt")

    def open_create_window(self):
        if self.create_window and self.create_window.winfo_exists():
            self.create_window.focus()
            self.create_window.lift()
            return

        self.create_window = ctk.CTkToplevel(self.app)
        self.create_window.title("서버 제작")
        self.create_window.geometry("1120x720+90+80")
        self.create_window.minsize(980, 640)
        self.create_window.configure(fg_color=BG_COLOR)
        self.create_window.grab_set()
        self.create_window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.create_window.grid_columnconfigure(1, weight=1)
        self.create_window.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()
        self.load_forge_versions_async()

    def close_window(self):
        if self.create_window and self.create_window.winfo_exists():
            self.create_window.destroy()
        self.create_window = None

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self.create_window,
            width=300,
            fg_color=PANEL_COLOR,
            corner_radius=24,
            border_width=1,
            border_color="#243128",
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(22, 12), pady=22)
        sidebar.grid_propagate(False)

        title = ctk.CTkLabel(
            sidebar,
            text="Create Server",
            font=(FONT, 32, "bold"),
            text_color=TEXT_COLOR,
        )
        title.pack(anchor="w", padx=24, pady=(28, 8))

        subtitle = ctk.CTkLabel(
            sidebar,
            text="새 서버 생성 화면만 따로 정리했습니다.\nForge는 Maven 메타데이터 기준으로 버전을 채웁니다.",
            font=(FONT, 14),
            text_color=MUTED_TEXT,
            justify="left",
        )
        subtitle.pack(anchor="w", padx=24)

        self._make_info_card(
            sidebar,
            "Forge",
            "자동 버전 목록",
            "공식 Maven 메타데이터를 읽고, 선택한 빌드 installer 링크를 바로 다운로드합니다.",
        )
        self._make_info_card(
            sidebar,
            "Paper",
            "수동 링크 입력",
            "버전은 빠르게 고르고, 실제 다운로드 링크만 붙여넣는 방식으로 정리했습니다.",
        )
        self._make_info_card(
            sidebar,
            "Fabric",
            "수동 링크 입력",
            "버전 리스트를 미리 보고 필요한 서버 링크만 넣어 받는 구조입니다.",
        )

        footer = ctk.CTkFrame(sidebar, fg_color=PANEL_ALT_COLOR, corner_radius=18)
        footer.pack(fill="x", padx=20, pady=(8, 22))

        footer_title = ctk.CTkLabel(
            footer,
            text="다운로드 메모",
            font=(FONT, 14, "bold"),
            text_color=TEXT_COLOR,
        )
        footer_title.pack(anchor="w", padx=16, pady=(14, 6))

        footer_text = ctk.CTkLabel(
            footer,
            text="다운로드 파일은 이 보관 폴더의 downloads에 저장합니다.",
            font=(FONT, 12),
            text_color=MUTED_TEXT,
            justify="left",
            wraplength=240,
        )
        footer_text.pack(anchor="w", padx=16, pady=(0, 14))

    def _make_info_card(self, parent, title, badge, description):
        card = ctk.CTkFrame(parent, fg_color=PANEL_ALT_COLOR, corner_radius=18)
        card.pack(fill="x", padx=20, pady=(18, 0))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 6))

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=(FONT, 18, "bold"),
            text_color=TEXT_COLOR,
        )
        title_label.pack(side="left")

        badge_label = ctk.CTkLabel(
            header,
            text=badge,
            font=(FONT, 11, "bold"),
            text_color=BG_COLOR,
            fg_color=ACCENT_COLOR,
            corner_radius=999,
            padx=10,
            pady=4,
        )
        badge_label.pack(side="right")

        body = ctk.CTkLabel(
            card,
            text=description,
            font=(FONT, 12),
            text_color=MUTED_TEXT,
            justify="left",
            wraplength=240,
        )
        body.pack(anchor="w", padx=16, pady=(0, 16))

    def _build_content(self):
        content = ctk.CTkFrame(self.create_window, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=(0, 22), pady=22)
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(content, fg_color=PANEL_COLOR, corner_radius=24)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        hero_left = ctk.CTkFrame(hero, fg_color="transparent")
        hero_left.pack(side="left", fill="both", expand=True, padx=24, pady=20)

        hero_title = ctk.CTkLabel(
            hero_left,
            text="서버 생성 UI Preview",
            font=(FONT, 28, "bold"),
            text_color=TEXT_COLOR,
        )
        hero_title.pack(anchor="w")

        hero_text = ctk.CTkLabel(
            hero_left,
            text="탭별 역할을 분리하고, 버전 선택 흐름이 한눈에 보이도록 다시 배치했습니다.",
            font=(FONT, 13),
            text_color=MUTED_TEXT,
            justify="left",
        )
        hero_text.pack(anchor="w", pady=(6, 0))

        hero_badge = ctk.CTkLabel(
            hero,
            text="clean layout",
            font=(FONT, 12, "bold"),
            text_color=BG_COLOR,
            fg_color=WARN_COLOR,
            corner_radius=999,
            padx=14,
            pady=8,
        )
        hero_badge.pack(side="right", padx=24)

        self.tabview = ctk.CTkTabview(
            content,
            fg_color=PANEL_COLOR,
            corner_radius=24,
            segmented_button_fg_color=PANEL_ALT_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_hover_color="#314536",
            text_color=TEXT_COLOR,
            anchor="nw",
        )
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("Forge")
        self.tabview.add("Paper")
        self.tabview.add("Fabric")

        self._build_forge_tab(self.tabview.tab("Forge"))
        self._build_manual_tab(
            self.tabview.tab("Paper"),
            title="Paper quick download",
            versions=self.paper_versions,
            site_url="https://papermc.io/downloads/all",
            placeholder="Paper 서버 JAR 링크를 붙여넣으세요",
            helper="필요한 마인크래프트 버전을 먼저 고르고, Paper 다운로드 링크만 붙여넣으면 됩니다.",
        )
        self._build_manual_tab(
            self.tabview.tab("Fabric"),
            title="Fabric quick download",
            versions=self.fabric_versions,
            site_url="https://fabricmc.net/use/server/",
            placeholder="Fabric 서버 링크를 붙여넣으세요",
            helper="Fabric 버전을 먼저 고른 뒤 서버 다운로드 링크를 붙여넣는 흐름입니다.",
        )

    def _build_forge_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 10))
        header.grid_columnconfigure(0, weight=1)

        header_text = ctk.CTkLabel(
            header,
            text="Forge는 마인크래프트 버전과 Forge 빌드를 따로 나눠서 선택합니다.",
            font=(FONT, 13),
            text_color=MUTED_TEXT,
        )
        header_text.grid(row=0, column=0, sticky="w")

        self.forge_status = ctk.CTkLabel(
            header,
            text="버전 목록 불러오는 중...",
            font=(FONT, 12),
            text_color=ACCENT_COLOR,
        )
        self.forge_status.grid(row=1, column=0, sticky="w", pady=(8, 0))

        refresh_button = ctk.CTkButton(
            header,
            text="새로고침",
            width=100,
            height=38,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=BG_COLOR,
            font=(FONT, 13, "bold"),
            command=self.load_forge_versions_async,
        )
        refresh_button.grid(row=0, column=1, rowspan=2, sticky="e")

        version_card = ctk.CTkFrame(tab, fg_color=PANEL_ALT_COLOR, corner_radius=20)
        version_card.grid(row=1, column=0, sticky="nsew", padx=(18, 9), pady=(0, 18))
        version_card.grid_rowconfigure(2, weight=1)
        version_card.grid_columnconfigure(0, weight=1)

        version_title = ctk.CTkLabel(
            version_card,
            text="Minecraft Version",
            font=(FONT, 18, "bold"),
            text_color=TEXT_COLOR,
        )
        version_title.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        self.forge_search = ctk.CTkEntry(
            version_card,
            placeholder_text="1.20, 1.21 검색",
            height=40,
            fg_color=PANEL_COLOR,
            border_width=1,
            border_color="#3A4E40",
            text_color=TEXT_COLOR,
            font=(FONT, 13),
        )
        self.forge_search.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.forge_search.bind("<KeyRelease>", self.filter_forge_versions)

        self.forge_version_frame = ctk.CTkScrollableFrame(
            version_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self.forge_version_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.forge_version_frame.grid_columnconfigure(0, weight=1)

        build_card = ctk.CTkFrame(tab, fg_color=PANEL_ALT_COLOR, corner_radius=20)
        build_card.grid(row=1, column=1, sticky="nsew", padx=(9, 18), pady=(0, 18))
        build_card.grid_rowconfigure(2, weight=1)
        build_card.grid_columnconfigure(0, weight=1)

        summary = ctk.CTkFrame(build_card, fg_color=PANEL_COLOR, corner_radius=18)
        summary.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        summary.grid_columnconfigure((0, 1, 2), weight=1)

        self.forge_mc_label = self._make_summary_box(summary, 0, "선택 버전", "-")
        self.forge_build_label = self._make_summary_box(summary, 1, "선택 빌드", "-")
        self.forge_count_label = self._make_summary_box(summary, 2, "빌드 개수", "0")

        build_title = ctk.CTkLabel(
            build_card,
            text="Forge Build",
            font=(FONT, 18, "bold"),
            text_color=TEXT_COLOR,
        )
        build_title.grid(row=1, column=0, sticky="w", padx=18)

        self.forge_build_frame = ctk.CTkScrollableFrame(
            build_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self.forge_build_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(10, 12))
        self.forge_build_frame.grid_columnconfigure(0, weight=1)

        action = ctk.CTkFrame(build_card, fg_color=PANEL_COLOR, corner_radius=18)
        action.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        action.grid_columnconfigure(0, weight=1)

        action_title = ctk.CTkLabel(
            action,
            text="Installer URL",
            font=(FONT, 13, "bold"),
            text_color=TEXT_COLOR,
        )
        action.grid_columnconfigure(0, weight=1)
        action_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.forge_url_entry = ctk.CTkEntry(
            action,
            height=40,
            state="readonly",
            fg_color=BG_COLOR,
            border_width=0,
            text_color=MUTED_TEXT,
            font=(FONT, 12),
        )
        self.forge_url_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

        download_button = ctk.CTkButton(
            action,
            text="선택한 Forge 다운로드",
            height=42,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=BG_COLOR,
            font=(FONT, 14, "bold"),
            command=self.download_selected_forge,
        )
        download_button.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

    def _make_summary_box(self, parent, column, label, value):
        box = ctk.CTkFrame(parent, fg_color=PANEL_ALT_COLOR, corner_radius=14)
        box.grid(row=0, column=column, sticky="ew", padx=6, pady=6)

        label_widget = ctk.CTkLabel(
            box,
            text=label,
            font=(FONT, 11),
            text_color=MUTED_TEXT,
        )
        label_widget.pack(anchor="w", padx=12, pady=(10, 4))

        value_widget = ctk.CTkLabel(
            box,
            text=value,
            font=(FONT, 16, "bold"),
            text_color=TEXT_COLOR,
        )
        value_widget.pack(anchor="w", padx=12, pady=(0, 10))
        return value_widget

    def _build_manual_tab(self, tab, title, versions, site_url, placeholder, helper):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(tab, fg_color=PANEL_ALT_COLOR, corner_radius=20)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 9), pady=18)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        left_title = ctk.CTkLabel(
            left,
            text=title,
            font=(FONT, 18, "bold"),
            text_color=TEXT_COLOR,
        )
        left_title.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 12))

        version_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        version_list.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        version_list.grid_columnconfigure(0, weight=1)

        selected_var = ctk.StringVar(value=versions[0] if versions else "")

        def select_version(version):
            selected_var.set(version)
            selected_label.configure(text=version or "-")

        for version in versions[:80]:
            button = ctk.CTkButton(
                version_list,
                text=version,
                height=38,
                fg_color=PANEL_COLOR,
                hover_color="#304235",
                text_color=TEXT_COLOR,
                font=(FONT, 13),
                anchor="w",
                command=lambda value=version: select_version(value),
            )
            button.grid(sticky="ew", padx=6, pady=4)

        right = ctk.CTkFrame(tab, fg_color=PANEL_ALT_COLOR, corner_radius=20)
        right.grid(row=0, column=1, sticky="nsew", padx=(9, 18), pady=18)
        right.grid_columnconfigure(0, weight=1)

        helper_title = ctk.CTkLabel(
            right,
            text="선택한 버전",
            font=(FONT, 12),
            text_color=MUTED_TEXT,
        )
        helper_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        selected_label = ctk.CTkLabel(
            right,
            text=selected_var.get() or "-",
            font=(FONT, 26, "bold"),
            text_color=TEXT_COLOR,
        )
        selected_label.grid(row=1, column=0, sticky="w", padx=20)

        helper_label = ctk.CTkLabel(
            right,
            text=helper,
            font=(FONT, 13),
            text_color=MUTED_TEXT,
            justify="left",
            wraplength=520,
        )
        helper_label.grid(row=2, column=0, sticky="w", padx=20, pady=(8, 18))

        url_entry = ctk.CTkEntry(
            right,
            placeholder_text=placeholder,
            height=42,
            fg_color=PANEL_COLOR,
            border_width=1,
            border_color="#3A4E40",
            text_color=TEXT_COLOR,
            font=(FONT, 13),
        )
        url_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))

        open_site_button = ctk.CTkButton(
            right,
            text="다운로드 사이트 열기",
            height=42,
            fg_color="#F2F4EE",
            hover_color="#DFE5D7",
            text_color=BG_COLOR,
            font=(FONT, 14, "bold"),
            command=lambda: webbrowser.open(site_url),
        )
        open_site_button.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        download_button = ctk.CTkButton(
            right,
            text="링크로 다운로드",
            height=42,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color=BG_COLOR,
            font=(FONT, 14, "bold"),
            command=lambda: self._download_manual_url(url_entry.get().strip(), selected_var.get()),
        )
        download_button.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 20))

    def load_forge_versions_async(self):
        if not self.create_window or not self.create_window.winfo_exists():
            return

        self.forge_status.configure(text="버전 목록 불러오는 중...", text_color=ACCENT_COLOR)
        thread = threading.Thread(target=self._load_forge_versions, daemon=True)
        thread.start()

    def _load_forge_versions(self):
        try:
            versions = self._fetch_forge_versions_from_xml()
            source = "공식 Maven 메타데이터"
        except Exception as remote_error:
            try:
                versions = self._load_forge_versions_from_backup()
                source = "로컬 백업 JSON"
            except Exception as backup_error:
                message = f"Forge 버전 로드 실패: {backup_error or remote_error}"
                self.app.after(0, lambda: self._set_forge_error(message))
                return

        self.app.after(0, lambda: self._apply_forge_versions(versions, source))

    def _fetch_forge_versions_from_xml(self):
        response = requests.get(FORGE_METADATA_URL, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        raw_versions = []
        for node in root.findall(".//version"):
            if node.text:
                value = node.text.strip()
                if "-" in value:
                    raw_versions.append(value)

        grouped = {}
        for version in raw_versions:
            mc_version = version.split("-", 1)[0]
            grouped.setdefault(mc_version, []).append(version)

        return {
            key: sorted(set(values), key=self._version_key, reverse=True)
            for key, values in grouped.items()
        }

    def _load_forge_versions_from_backup(self):
        with (DATA_ROOT / "forge_versions.json").open("r", encoding="utf-8") as file:
            data = json.load(file)

        grouped = {}
        for mc_version, info in data.items():
            builds = list(info.get("versions", {}).keys())
            if builds:
                grouped[mc_version] = sorted(builds, key=self._version_key, reverse=True)

        if not grouped:
            raise ValueError("Forge 백업 데이터가 비어 있습니다.")
        return grouped

    def _apply_forge_versions(self, versions, source):
        if not self.create_window or not self.create_window.winfo_exists():
            return

        self.forge_versions = {
            key: versions[key] for key in sorted(versions.keys(), key=self._version_key, reverse=True)
        }
        self.forge_status.configure(
            text=f"{len(self.forge_versions)}개 마인크래프트 버전 로드 완료 · {source}",
            text_color=MUTED_TEXT,
        )
        self.filter_forge_versions()

    def _set_forge_error(self, message):
        if not self.create_window or not self.create_window.winfo_exists():
            return
        self.forge_status.configure(text=message, text_color=WARN_COLOR)

    def filter_forge_versions(self, _event=None):
        query = self.forge_search.get().strip().lower() if hasattr(self, "forge_search") else ""
        versions = [
            version for version in self.forge_versions.keys()
            if query in version.lower()
        ]
        self._render_forge_version_buttons(versions)

    def _render_forge_version_buttons(self, versions):
        for widget in self.forge_version_frame.winfo_children():
            widget.destroy()

        if not versions:
            empty = ctk.CTkLabel(
                self.forge_version_frame,
                text="검색 결과가 없습니다.",
                font=(FONT, 13),
                text_color=MUTED_TEXT,
            )
            empty.grid(padx=8, pady=12)
            self._render_forge_build_buttons([])
            return

        current = self.forge_selected_mc if self.forge_selected_mc in versions else versions[0]
        self.forge_selected_mc = current

        for version in versions:
            count = len(self.forge_versions.get(version, []))
            selected = version == current
            button = ctk.CTkButton(
                self.forge_version_frame,
                text=f"{version}  ({count})",
                height=42,
                fg_color=ACCENT_COLOR if selected else PANEL_COLOR,
                hover_color=ACCENT_HOVER if selected else "#304235",
                text_color=BG_COLOR if selected else TEXT_COLOR,
                font=(FONT, 13, "bold" if selected else "normal"),
                anchor="w",
                command=lambda value=version: self.select_forge_version(value),
            )
            button.grid(sticky="ew", padx=6, pady=4)

        self.select_forge_version(current)

    def select_forge_version(self, version):
        self.forge_selected_mc = version
        builds = self.forge_versions.get(version, [])
        self.forge_mc_label.configure(text=version or "-")
        self.forge_count_label.configure(text=str(len(builds)))
        self._render_forge_version_buttons_if_needed()
        self._render_forge_build_buttons(builds)

    def _render_forge_version_buttons_if_needed(self):
        for widget in self.forge_version_frame.winfo_children():
            if not isinstance(widget, ctk.CTkButton):
                continue
            is_selected = widget.cget("text").startswith(f"{self.forge_selected_mc}  ")
            widget.configure(
                fg_color=ACCENT_COLOR if is_selected else PANEL_COLOR,
                hover_color=ACCENT_HOVER if is_selected else "#304235",
                text_color=BG_COLOR if is_selected else TEXT_COLOR,
                font=(FONT, 13, "bold" if is_selected else "normal"),
            )

    def _render_forge_build_buttons(self, builds):
        for widget in self.forge_build_frame.winfo_children():
            widget.destroy()

        if not builds:
            self.forge_selected_build = ""
            self.forge_build_label.configure(text="-")
            self._set_forge_url("")
            empty = ctk.CTkLabel(
                self.forge_build_frame,
                text="선택 가능한 Forge 빌드가 없습니다.",
                font=(FONT, 13),
                text_color=MUTED_TEXT,
            )
            empty.grid(padx=8, pady=12)
            return

        current_build = self.forge_selected_build if self.forge_selected_build in builds else builds[0]
        self.forge_selected_build = current_build

        for build in builds:
            selected = build == current_build
            button = ctk.CTkButton(
                self.forge_build_frame,
                text=build,
                height=42,
                fg_color=ACCENT_COLOR if selected else PANEL_COLOR,
                hover_color=ACCENT_HOVER if selected else "#304235",
                text_color=BG_COLOR if selected else TEXT_COLOR,
                font=(FONT, 13, "bold" if selected else "normal"),
                anchor="w",
                command=lambda value=build: self.select_forge_build(value),
            )
            button.grid(sticky="ew", padx=6, pady=4)

        self.select_forge_build(current_build)

    def select_forge_build(self, build):
        self.forge_selected_build = build
        self.forge_build_label.configure(text=build or "-")
        self._set_forge_url(self._forge_download_url(build) if build else "")

        for widget in self.forge_build_frame.winfo_children():
            if not isinstance(widget, ctk.CTkButton):
                continue
            is_selected = widget.cget("text") == build
            widget.configure(
                fg_color=ACCENT_COLOR if is_selected else PANEL_COLOR,
                hover_color=ACCENT_HOVER if is_selected else "#304235",
                text_color=BG_COLOR if is_selected else TEXT_COLOR,
                font=(FONT, 13, "bold" if is_selected else "normal"),
            )

    def download_selected_forge(self):
        if not self.forge_selected_build:
            self.forge_status.configure(text="Forge 빌드를 먼저 선택해주세요.", text_color=WARN_COLOR)
            return

        url = self._forge_download_url(self.forge_selected_build)
        self.forge_status.configure(
            text=f"{self.forge_selected_build} 다운로드를 시작합니다.",
            text_color=ACCENT_COLOR,
        )
        self._download_file(url)

    def _download_manual_url(self, url, selected_version):
        if not url:
            return
        self._download_file(url)
        if hasattr(self, "forge_status"):
            self.forge_status.configure(
                text=f"{selected_version or '선택한 버전'}과 연결된 링크 다운로드를 시작했습니다.",
                text_color=ACCENT_COLOR,
            )

    def _download_file(self, url):
        filename = Path(urlsplit(url).path).name
        if not filename:
            raise ValueError("다운로드 파일 이름을 확인할 수 없습니다.")

        DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        target_path = DOWNLOAD_ROOT / filename
        with requests.get(url, stream=True, timeout=(10, 300)) as response:
            response.raise_for_status()
            with target_path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)

    def _set_forge_url(self, url):
        self.forge_url_entry.configure(state="normal")
        self.forge_url_entry.delete(0, "end")
        self.forge_url_entry.insert(0, url)
        self.forge_url_entry.configure(state="readonly")

    def _forge_download_url(self, build):
        return f"{FORGE_BASE_URL}/{build}/forge-{build}-installer.jar"

    def _version_key(self, value):
        tokens = re.findall(r"\d+|[A-Za-z]+", value)
        return tuple((0, int(token)) if token.isdigit() else (1, token.lower()) for token in tokens)

    def _read_lines(self, path):
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]


class _PreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1x1+0+0")
        self.withdraw()
        self.creator = ServerCreateWindow(self)
        self.after(100, self.creator.open_create_window)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    preview = _PreviewApp()
    preview.mainloop()
