import tkinter as tk
from tkinter import ttk
import ctypes
import random
import math
import threading
import time

user32 = ctypes.windll.user32

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("mi", MOUSEINPUT)
    ]

INPUT_MOUSE = 0

LEFTDOWN = 0x0002
LEFTUP = 0x0004
RIGHTDOWN = 0x0008
RIGHTUP = 0x0010
MIDDLEDOWN = 0x0020
MIDDLEUP = 0x0040

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class AutoClicker:
    def __init__(self):

        self.cx = None
        self.cy = None
        self.r = None

        self.running = False
        self.hotkey = None
        self.waiting_key = False
        self.hotkey_just_set = False # اضافه کردن این متغیر برای رفع مشکل

        self.interval = 1 / 70
        self.clicks_done = 0

        self.root = tk.Tk()
        self.root.title("AltClicker")
        self.root.geometry("450x760")
        self.root.resizable(False, False)

        self.mode = tk.StringVar(value="cursor")
        self.click_btn = tk.StringVar(value="left")
        self.click_type = tk.StringVar(value="single")
        self.humanize = tk.BooleanVar(value=False)
        self.stop_after_var = tk.IntVar(value=0)

        self.gaming_mode_var = tk.BooleanVar(value=False)
        self.cps_var = tk.StringVar(value="70")

        self.build_ui()

        self.root.bind("<Key>", self.capture_key)

        threading.Thread(target=self.key_listener, daemon=True).start()
        threading.Thread(target=self.click_loop, daemon=True).start()

        self.update_status_label()

    def build_ui(self):

        style = ttk.Style()
        style.theme_use("clam")

        title_label = tk.Label(
        self.root,
        text="Ebrahim Khani",
        fg="#1e90ff",
        font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(10,0))

        subtitle_label = tk.Label(
        self.root,
        text="Develops by AltSafe",
        fg="#1e90ff",
        font=("Arial", 9)
        )
        subtitle_label.pack(pady=(0,8))

        title_label.pack(pady=(10,5))

        self.status = tk.Label(self.root,text="Status: OFF",fg="white",bg="red",font=("Arial",14,"bold"),width=20)
        self.status.pack(pady=10)

        hk_frame = ttk.LabelFrame(self.root,text="Hotkey Settings")
        hk_frame.pack(fill="x",padx=10,pady=5)

        self.hotkey_label = ttk.Label(hk_frame,text="Current Hotkey: None",font=("Arial",10,"bold"))
        self.hotkey_label.pack(pady=5)

        ttk.Button(hk_frame,text="Set Hotkey",command=self.set_hotkey).pack(pady=5)

        opts_frame = ttk.LabelFrame(self.root,text="Click Options")
        opts_frame.pack(fill="x",padx=10,pady=5)

        ttk.Label(opts_frame,text="Mouse Button:").grid(row=0,column=0,padx=5,pady=5,sticky="w")
        ttk.Combobox(opts_frame,textvariable=self.click_btn,values=["left","right","middle"],state="readonly",width=10).grid(row=0,column=1,padx=5,pady=5)

        ttk.Label(opts_frame,text="Click Type:").grid(row=0,column=2,padx=5,pady=5,sticky="w")
        ttk.Combobox(opts_frame,textvariable=self.click_type,values=["single","double"],state="readonly",width=10).grid(row=0,column=3,padx=5,pady=5)

        ttk.Checkbutton(opts_frame,text="Humanize (Random Jitter)",variable=self.humanize).grid(row=1,column=0,columnspan=2,padx=5,pady=5,sticky="w")

        speed_frame = ttk.LabelFrame(self.root,text="Click Interval (Speed)")
        speed_frame.pack(fill="x",padx=10,pady=5)

        ttk.Label(speed_frame,text="Max speed is limited to 70 Clicks Per Second",foreground="gray").grid(row=0,column=0,columnspan=8,pady=2)

        self.min_e = ttk.Entry(speed_frame,width=5)
        self.min_e.insert(0,"0")

        self.sec_e = ttk.Entry(speed_frame,width=5)
        self.sec_e.insert(0,"0")

        self.ms_e = ttk.Entry(speed_frame,width=5)
        self.ms_e.insert(0,"14")

        self.min_e.grid(row=1,column=0,padx=2)
        ttk.Label(speed_frame,text="m").grid(row=1,column=1)

        self.sec_e.grid(row=1,column=2,padx=2)
        ttk.Label(speed_frame,text="s").grid(row=1,column=3)

        self.ms_e.grid(row=1,column=4,padx=2)
        ttk.Label(speed_frame,text="ms").grid(row=1,column=5)

        ttk.Button(speed_frame,text="Apply Speed",command=self.apply_speed).grid(row=1,column=6,padx=10,pady=5)

        gaming_mode_frame = ttk.LabelFrame(self.root,text="Gaming Mode")
        gaming_mode_frame.pack(fill="x",padx=10,pady=5)

        self.gaming_mode_checkbox = ttk.Checkbutton(
            gaming_mode_frame,
            text="Enable Gaming Mode",
            variable=self.gaming_mode_var,
            command=self.toggle_gaming_mode
        )
        self.gaming_mode_checkbox.pack(anchor="w",padx=5,pady=5)

        self.cps_options_frame = ttk.Frame(gaming_mode_frame)
        self.cps_options_frame.pack(anchor="w",padx=5,pady=5)

        ttk.Radiobutton(self.cps_options_frame,text="90 CPS",variable=self.cps_var,value="90",command=lambda:self.set_gaming_cps(90)).pack(side="left",padx=5)
        ttk.Radiobutton(self.cps_options_frame,text="80 CPS",variable=self.cps_var,value="80",command=lambda:self.set_gaming_cps(80)).pack(side="left",padx=5)
        ttk.Radiobutton(self.cps_options_frame,text="70 CPS",variable=self.cps_var,value="70",command=lambda:self.set_gaming_cps(70)).pack(side="left",padx=5)

        self.cps_options_frame_row2 = ttk.Frame(gaming_mode_frame)
        self.cps_options_frame_row2.pack(anchor="w",padx=5,pady=5)

        ttk.Radiobutton(self.cps_options_frame_row2,text="60 CPS",variable=self.cps_var,value="60",command=lambda:self.set_gaming_cps(60)).pack(side="left",padx=5)
        ttk.Radiobutton(self.cps_options_frame_row2,text="50 CPS",variable=self.cps_var,value="50",command=lambda:self.set_gaming_cps(50)).pack(side="left",padx=5)

        self.toggle_gaming_mode()

        pos_frame = ttk.LabelFrame(self.root,text="Cursor Position")
        pos_frame.pack(fill="x",padx=10,pady=5)

        ttk.Radiobutton(pos_frame,text="Current Cursor Position",variable=self.mode,value="cursor").pack(anchor="w",padx=5,pady=2)
        ttk.Radiobutton(pos_frame,text="Random Inside Circle",variable=self.mode,value="random").pack(anchor="w",padx=5,pady=2)

        ttk.Button(pos_frame,text="Select Circle Area",command=self.select_circle).pack(pady=5)

        stop_frame = ttk.LabelFrame(self.root,text="Stop Condition")
        stop_frame.pack(fill="x",padx=10,pady=5)

        ttk.Label(stop_frame,text="Stop after (0 = Infinite):").pack(side="left",padx=5,pady=5)
        ttk.Entry(stop_frame,textvariable=self.stop_after_var,width=10).pack(side="left",padx=5,pady=5)

        footer = tk.Label(
            self.root,
            text="by AltSafe",
            fg="gray",
            font=("Arial",8)
        )
        footer.pack(side="bottom",pady=5)

    def set_gaming_cps(self,cps):
        if self.gaming_mode_var.get():
            self.interval = 1 / cps
            self.update_status_label()

    def toggle_gaming_mode(self):

        is_gaming_mode = self.gaming_mode_var.get()

        state_manual = "disabled" if is_gaming_mode else "normal"
        state_gaming = "normal" if is_gaming_mode else "disabled"

        self.min_e.config(state=state_manual)
        self.sec_e.config(state=state_manual)
        self.ms_e.config(state=state_manual)

        for w in self.cps_options_frame.winfo_children():
            w.config(state=state_gaming)

        for w in self.cps_options_frame_row2.winfo_children():
            w.config(state=state_gaming)

        if is_gaming_mode:
            self.set_gaming_cps(int(self.cps_var.get()))
        else:
            self.apply_speed()

        self.update_status_label()

    def apply_speed(self):

        if self.gaming_mode_var.get():
            return

        try:
            m = int(self.min_e.get() or "0")
            s = int(self.sec_e.get() or "0")
            ms = int(self.ms_e.get() or "0")

            total = m*60 + s + ms/1000

            if total <= 0:
                self.interval = 1/70
                return

            if total < 1/70:
                self.interval = 1/70
            else:
                self.interval = total

        except:
            self.interval = 1/70

        self.update_status_label()

    def set_hotkey(self):
        self.waiting_key = True
        self.hotkey_label.config(text="Press any key...")

    def capture_key(self,event):
        if self.waiting_key:
            self.hotkey = event.keycode
            self.waiting_key = False
            self.hotkey_label.config(text=f"Current Hotkey: {event.keysym.upper()}")
            # نشان می‌دهد که هات‌کی تازه تنظیم شده است
            self.hotkey_just_set = True

    def toggle(self):
        self.running = not self.running
        self.clicks_done = 0
        self.update_status_label()

    def key_listener(self):

        key_pressed=False

        while True:

            if self.hotkey:
                # اگر هات‌کی تازه تنظیم شده باشد، فشار اولیه را نادیده می‌گیریم
                if self.hotkey_just_set:
                    key_pressed = True  # فرض می‌کنیم کلید فشرده شده است تا از فعال شدن ناخواسته جلوگیری شود
                    self.hotkey_just_set = False # پرچم را ریست می‌کنیم
                    # ادامه می‌دهیم تا وضعیت کلید واقعاً رها شود

                state=user32.GetAsyncKeyState(self.hotkey)

                if state & 0x8000: # کلید فشرده شده است
                    if not key_pressed:
                        self.root.after(0,self.toggle)
                        key_pressed=True

                else: # کلید رها شده است
                    key_pressed=False

            time.sleep(0.01)

    def select_circle(self):

        overlay=tk.Toplevel(self.root)

        overlay.attributes("-fullscreen",True)
        overlay.attributes("-alpha",0.3)
        overlay.configure(bg="black")
        overlay.config(cursor="cross")
        overlay.attributes("-topmost",True)

        canvas=tk.Canvas(overlay,bg="black",highlightthickness=0)
        canvas.pack(fill="both",expand=True)

        start={}

        def down(e):
            start["x"]=e.x
            start["y"]=e.y

        def drag(e):

            canvas.delete("circle")

            r=int(math.hypot(e.x-start["x"],e.y-start["y"]))

            canvas.create_oval(
                start["x"]-r,
                start["y"]-r,
                start["x"]+r,
                start["y"]+r,
                outline="red",
                width=3,
                tag="circle"
            )

        def up(e):

            self.cx=start["x"]
            self.cy=start["y"]
            self.r=int(math.hypot(e.x-start["x"],e.y-start["y"]))

            overlay.destroy()

            self.mode.set("random")

        canvas.bind("<ButtonPress-1>",down)
        canvas.bind("<B1-Motion>",drag)
        canvas.bind("<ButtonRelease-1>",up)

    def perform_click(self,x,y):

        user32.SetCursorPos(x,y)

        btn=self.click_btn.get()

        down,up=LEFTDOWN,LEFTUP

        if btn=="right":
            down,up=RIGHTDOWN,RIGHTUP

        elif btn=="middle":
            down,up=MIDDLEDOWN,MIDDLEUP

        down_input=INPUT(INPUT_MOUSE,MOUSEINPUT(0,0,0,down,0,None))
        up_input=INPUT(INPUT_MOUSE,MOUSEINPUT(0,0,0,up,0,None))

        user32.SendInput(1,ctypes.byref(down_input),ctypes.sizeof(INPUT))
        user32.SendInput(1,ctypes.byref(up_input),ctypes.sizeof(INPUT))

    def click(self,x,y):

        self.perform_click(x,y)

        if self.click_type.get()=="double":
            time.sleep(0.01)
            self.perform_click(x,y)

    def click_loop(self):

        pt=POINT()

        while True:

            if not self.running:
                time.sleep(0.01)
                continue

            start=time.perf_counter()

            limit=self.stop_after_var.get()

            if limit>0 and self.clicks_done>=limit:
                self.root.after(0,self.toggle)
                continue

            if self.mode.get()=="cursor":

                user32.GetCursorPos(ctypes.byref(pt))
                x,y=pt.x,pt.y

            else:

                if self.cx is None:
                    user32.GetCursorPos(ctypes.byref(pt))
                    x,y=pt.x,pt.y
                else:
                    angle=random.uniform(0,2*math.pi)
                    radius=self.r*math.sqrt(random.random())
                    x=int(self.cx+radius*math.cos(angle))
                    y=int(self.cy+radius*math.sin(angle))

            self.click(x,y)

            self.clicks_done+=1

            wait=self.interval

            if self.humanize.get():
                wait+=random.uniform(0.005,0.02)

            elapsed=time.perf_counter()-start

            time.sleep(max(0,wait-elapsed))

    def update_status_label(self):

        if self.running:
            self.status.config(text="Status: ON",bg="green")

        elif self.gaming_mode_var.get():

            cps=self.cps_var.get()

            self.status.config(text=f"Status: Gaming Mode ({cps} CPS)",bg="blue")

        else:

            cps=round(1/self.interval,2)

            self.status.config(text=f"Status: Idle ({cps} CPS)",bg="gray")

    def run(self):
        self.root.mainloop()


if __name__=="__main__":
    AutoClicker().run()
