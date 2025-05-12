from PIL import Image, ImageColor
import customtkinter as ctk
import time

def hex_to_rgb(hex_color):
    return ImageColor.getrgb(hex_color)

def tint_image(image_path, hex_color, alpha=0.5):
    img = Image.open(image_path).convert("RGBA")
    rgb = ImageColor.getrgb(hex_color)

    # 투명 영역은 그대로 유지한 상태에서 색만 덮기
    r, g, b, a = img.split()
    overlay = Image.new("RGBA", img.size, rgb + (0,))  # 완전 투명한 색 레이어
    mask = a.point(lambda px: int(px * alpha))         # 알파만큼 덮기용 마스크
    color_overlay = Image.new("RGBA", img.size, rgb + (255,))
    overlay = Image.composite(color_overlay, overlay, mask)

    return Image.alpha_composite(img, overlay)


def make_image_button(master, image_path, command_func,
                      size=(50, 50),
                      base_color="#FFFFFF",
                      hover_color="#000000",
                      press_color="#FFFFFF",
                      alpha=0):
    img_base = tint_image(image_path, base_color, alpha)
    img_hover = tint_image(image_path, hover_color, 0.33)
    img_press = tint_image(image_path, press_color, alpha)

    ctk_img_base = ctk.CTkImage(img_base, size=size)
    ctk_img_hover = ctk.CTkImage(img_hover, size=size)
    ctk_img_press = ctk.CTkImage(img_press, size=size)

    label = ctk.CTkLabel(master, image=ctk_img_base, text="")
    label.image_set = {
        "base": ctk_img_base,
        "hover": ctk_img_hover,
        "press": ctk_img_press
    }

    def on_enter(e): label.configure(image=label.image_set["hover"])
    def on_leave(e): label.configure(image=label.image_set["base"])
    def on_press(e):
        label.configure(image=label.image_set["press"])
        command_func()

    def on_release(e):
        x, y = e.x, e.y
        w, h = label.winfo_width(), label.winfo_height()

        # 마우스가 버튼 안에 있는 경우 → hover 이미지로
        if 0 <= x < w and 0 <= y < h:
            label.configure(image=label.image_set["hover"])

        else:
            label.configure(image=label.image_set["base"])


    label.bind("<Enter>", on_enter)
    label.bind("<Leave>", on_leave)
    label.bind("<ButtonPress-1>", on_press)
    label.bind("<ButtonRelease-1>", on_release)

    return label
