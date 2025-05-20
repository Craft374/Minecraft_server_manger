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

class Server_create:
    def __init__(self, app):
        self.app = app  # ServerManagerApp 인스턴스를 받아 저장
    def test(self):
        print("s")
    def open_create_window(self):
        create_window = ctk.CTkToplevel(self.app)
        create_window.title("서버 제작")
        create_window.geometry("850x510+75+100")
        create_window.grab_set()