import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("400x800")
app.title("색상 이름 미리보기")

colors = [
    "white", "black", "gray", "light gray", "dark gray", "red", "green", "blue",
    "cyan", "magenta", "yellow", "orange", "pink", "purple", "brown", "turquoise",
    "gold", "silver", "navy", "sky blue", "lime", "olive", "maroon", "teal",
    "indigo", "violet", "beige", "salmon", "coral", "chocolate", "tan", "plum",
    "orchid", "crimson"
]

for color in colors:
    try:
        label = ctk.CTkLabel(app, text=color, text_color=color)
        label.pack(anchor="w", padx=10, pady=2)
    except Exception as e:
        print(f"'{color}' is not supported: {e}")

app.mainloop()
