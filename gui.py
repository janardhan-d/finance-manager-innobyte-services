import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import os
import matplotlib.pyplot as plt
from tkcalendar import DateEntry
from database import get_user_id
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")

from auth import register_user, login_user, update_profile_pic, get_profile_pic
from transactions import add_transaction, view_transactions, update_transaction, delete_transaction, search_transactions
from reports import monthly_report, yearly_report, monthly_trend, category_breakdown
from budget import set_budget, check_budget, get_budget_progress, list_budgets
from backup import backup_database, restore_database
from database import setup_database

APP_COLORS = {
    "bg": "#07111f",
    "surface": "#0f172a",
    "surface_alt": "#13233d",
    "panel": "#152542",
    "border": "#2c4b72",
    "accent": "#00e5ff",
    "accent_soft": "#6fe7ff",
    "text": "#f7fbff",
    "muted": "#94a3b8",
    "hover": "#11324d",
    "danger": "#ff6b6b",
    "success": "#33d17a",
    "sidebar": "#060b14",
    "sidebar_text": "#f7fbff"
}


def get_user_totals(user_id):
    transactions = view_transactions(user_id)
    total_income = 0
    total_expense = 0

    for t in transactions:
        amount = float(t[1])
        t_type = t[3]

        if t_type.lower() == "income":
            total_income += amount
        else:
            total_expense += amount

    balance = total_income - total_expense
    return total_income, total_expense, balance

# `get_user_id` provided by database.get_user_id

# ---------------------------------------------------------
# CREATE ICONS FOLDER
# ---------------------------------------------------------
if not os.path.exists(ICONS_DIR):
    os.makedirs(ICONS_DIR)

# ---------------------------------------------------------
# GENERATE REAL VECTOR-STYLE ICONS
# ---------------------------------------------------------
def create_icon(path, shape):
    if path.startswith("icons/") or path.startswith("icons\\"):
        path = os.path.basename(path)
    icon_path = os.path.join(ICONS_DIR, path)
    img = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Cyan → Blue gradient
    for i in range(60):
        g = int(229 + (123 - 229) * (i / 60))
        draw.line([(0, i), (60, i)], fill=(0, g, 255))

    # Shapes
    if shape == "home":
        draw.rectangle((15, 30, 45, 50), fill="white")
        draw.polygon([(15, 30), (30, 15), (45, 30)], fill="white")

    elif shape == "plus":
        draw.rectangle((27, 10, 33, 50), fill="white")
        draw.rectangle((10, 27, 50, 33), fill="white")

    elif shape == "list":
        for y in [15, 28, 41]:
            draw.rectangle((15, y, 45, y + 6), fill="white")

    elif shape == "calendar":
        draw.rectangle((10, 20, 50, 50), outline="white", width=3)
        draw.rectangle((10, 20, 50, 30), fill="white")

    elif shape == "wallet":
        draw.rectangle((10, 20, 50, 45), outline="white", width=3)
        draw.rectangle((35, 25, 45, 35), fill="white")

    elif shape == "check":
        draw.line((15, 35, 25, 45), fill="white", width=5)
        draw.line((25, 45, 45, 20), fill="white", width=5)

    elif shape == "power":
        draw.arc((15, 15, 45, 45), start=45, end=315, fill="white", width=5)
        draw.rectangle((27, 10, 33, 30), fill="white")

    elif shape == "person":
        draw.ellipse((22, 12, 38, 28), fill="white")
        draw.ellipse((16, 30, 44, 52), fill="white")

    elif shape == "archive":
        draw.rounded_rectangle((12, 18, 48, 50), radius=4, outline="white", width=3)
        draw.rectangle((18, 14, 42, 20), fill="white")
        draw.rectangle((22, 20, 38, 44), fill="white")

    elif shape == "undo":
        draw.arc((12, 18, 44, 44), start=40, end=220, fill="white", width=4)
        draw.polygon([(14, 18), (8, 24), (16, 24)], fill="white")

    img.save(path)

# Generate icons
create_icon("dashboard.png", "home")
create_icon("add.png", "plus")
create_icon("view.png", "list")
create_icon("month.png", "calendar")
create_icon("year.png", "calendar")
create_icon("budget.png", "wallet")
create_icon("check.png", "check")
create_icon("profile.png", "person")
create_icon("backup.png", "archive")
create_icon("restore.png", "undo")
create_icon("logout.png", "power")

# ---------------------------------------------------------
# PLACEHOLDER ENTRY
# ---------------------------------------------------------
class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder="", color="grey", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["foreground"]
        self._is_placeholder = False

        self.bind("<FocusIn>", self._clear)
        self.bind("<FocusOut>", self._add)

        self._add()

    def get(self):
        if self._is_placeholder:
            return ""
        return super().get()

    def _clear(self, event=None):
        if self._is_placeholder:
            self.delete(0, tk.END)
            self["foreground"] = self.default_fg_color
            self._is_placeholder = False

    def _add(self, event=None):
        if not super().get():
            self.insert(0, self.placeholder)
            self["foreground"] = self.placeholder_color
            self._is_placeholder = True

# ---------------------------------------------------------
# PASSWORD ENTRY WITH EYE TOGGLE
# ---------------------------------------------------------
class PasswordEntry(ttk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, show="*", **kwargs)
        self.showing = False

    def toggle(self):
        self.config(show="" if not self.showing else "*")
        self.showing = not self.showing


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)

    def show(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 22
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify="left",
            background="#13233d",
            foreground="#f7fbff",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=1)

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ---------------------------------------------------------
# FROSTED GLASS PANEL (Cyan Tint, 12px Blur, 70% Transparent)
# ---------------------------------------------------------
def create_frosted_panel(width, height):
    blur = 12
    transparency = 180  # 70%

    base = Image.new("RGBA", (width, height), (0, 255, 255, transparency))
    blurred = base.filter(ImageFilter.GaussianBlur(blur))

    # Rounded corners
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=25, fill=255)
    blurred.putalpha(mask)

    # Cyan border
    border = Image.new("RGBA", (width, height), (0, 255, 255, 255))
    border_mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(border_mask)
    draw.rounded_rectangle((0, 0, width, height), radius=25, outline=255, width=2)
    border.putalpha(border_mask)

    final = Image.alpha_composite(blurred, border)
    return ImageTk.PhotoImage(final)

# ---------------------------------------------------------
# MAIN APPLICATION CLASS
# ---------------------------------------------------------
class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finance Manager")
        self.root.geometry("1080x720")
        self.root.minsize(960, 680)
        self.colors = APP_COLORS.copy()
        self.theme = "dark"
        self.last_login_time = None
        self.current_page = None
        self.apply_global_styles()

        setup_database()
        self.logged_in_user = None
        self.sidebar_expanded = False

        self.splash_screen()

    def apply_global_styles(self):
        self.root.configure(bg=self.colors["bg"])
        self.root.option_add("*Font", ("Segoe UI", 11))
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=(10, 6), borderwidth=0, relief="flat", background=self.colors["panel"], foreground=self.colors["text"])
        style.map("TButton", background=[("active", self.colors["hover"])])
        style.configure("TEntry", fieldbackground=self.colors["surface"], foreground=self.colors["text"], bordercolor=self.colors["border"])
        style.configure("TLabelframe", background=self.colors["bg"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Treeview", background=self.colors["surface"], foreground=self.colors["text"], fieldbackground=self.colors["surface"], rowheight=26)
        style.configure("Treeview.Heading", background=self.colors["surface_alt"], foreground=self.colors["text"], relief="flat")
        style.map("Treeview", background=[("selected", self.colors["accent"])])

    def create_panel(self, parent, **kwargs):
        defaults = {
            "bg": self.colors["surface"],
            "highlightbackground": self.colors["border"],
            "highlightthickness": 1
        }
        defaults.update(kwargs)
        return tk.Frame(parent, **defaults)

    def attach_tooltip(self, widget, text):
        ToolTip(widget, text)

    def create_date_picker(self, parent, initial=None, width=20):
        picker = DateEntry(
            parent,
            width=width,
            background=self.colors["accent"],
            foreground=self.colors["bg"],
            borderwidth=2,
            date_pattern="yyyy-mm-dd"
        )
        if initial:
            try:
                picker.set_date(initial)
            except Exception:
                pass
        return picker

    def normalize_month_value(self, value):
        if not value:
            return value
        try:
            parsed = datetime.datetime.strptime(str(value), "%Y-%m-%d")
        except ValueError:
            try:
                parsed = datetime.datetime.strptime(str(value), "%Y-%m")
            except ValueError:
                return value
        return parsed.strftime("%Y-%m")

    # -----------------------------------------------------
    # HOVER EFFECT FOR SIDEBAR BUTTONS
    # -----------------------------------------------------
    def apply_hover_effect(self, widget, highlight=None, active=False):
        def on_enter(e):
            widget.config(bg=self.colors["hover"], fg=self.colors["accent"])
            if highlight is not None:
                self.animate_bar(highlight, 6)

        def on_leave(e):
            self.set_button_state(widget, highlight, active)

        def on_press(e):
            if isinstance(widget, tk.Button):
                widget.config(bg=self.colors["surface_alt"], fg=self.colors["accent"])

        def on_release(e):
            self.set_button_state(widget, highlight, active)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<ButtonPress-1>", on_press)
        widget.bind("<ButtonRelease-1>", on_release)

    def set_button_state(self, widget, highlight=None, active=False):
        widget.config(bg=self.colors["hover"] if active else self.colors["sidebar"], fg=self.colors["accent"] if active else self.colors["sidebar_text"])
        if highlight is not None:
            self.animate_bar(highlight, 6 if active else 0)

    def animate_bar(self, bar, target_width, step=2, delay=8):
        try:
            current_width = bar.winfo_width()
        except Exception:
            current_width = 0
        if current_width < target_width:
            new_width = min(current_width + step, target_width)
        elif current_width > target_width:
            new_width = max(current_width - step, target_width)
        else:
            return
        bar.configure(width=new_width)
        bar.after(delay, lambda: self.animate_bar(bar, target_width, step, delay))

    # -----------------------------------------------------
    # SPLASH SCREEN
    # -----------------------------------------------------
    def splash_screen(self):
        self.login_screen()

    # -----------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------
    def set_sidebar_state(self, expanded):
        self.sidebar_expanded = expanded
        target_width = 210 if expanded else 70
        if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            self.sidebar.config(width=target_width)
        if hasattr(self, "menu_buttons") and hasattr(self, "menu_items"):
            for (frame, btn, _), menu_item in zip(self.menu_buttons, self.menu_items):
                text = menu_item[0]
                if getattr(btn, "winfo_exists", lambda: False)():
                    btn.config(text=text if expanded else "")
                if getattr(frame, "winfo_exists", lambda: False)():
                    frame.configure(width=target_width)

    def build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.set_sidebar_state(True)

        self.theme_button = tk.Button(
            self.sidebar,
            text="🌓",
            bg=self.colors["sidebar"],
            fg=self.colors["sidebar_text"],
            bd=0,
            relief="flat",
            command=self.toggle_theme
        )
        self.theme_button.pack(pady=6)
        self.attach_tooltip(self.theme_button, "Switch between light and dark mode")

        self.menu_items = [
            ("Dashboard", "icons/dashboard.png", self.dashboard, "Overview of your financial summary", "dashboard"),
            ("Profile", "icons/profile.png", self.profile_screen, "Manage your profile and photo", "profile"),
            ("Add Transaction", "icons/add.png", self.add_transaction_screen, "Log a new income or expense", "add_transaction"),
            ("View Transactions", "icons/view.png", self.view_transactions_screen, "Browse and manage your transactions", "view_transactions"),
            ("Monthly Report", "icons/month.png", self.monthly_report_screen, "Review your spending for a month", "monthly_report"),
            ("Yearly Report", "icons/year.png", self.yearly_report_screen, "Review your spending for a year", "yearly_report"),
            ("Set Budget", "icons/budget.png", self.set_budget_screen, "Create a monthly budget", "set_budget"),
            ("Check Budget", "icons/check.png", self.check_budget_screen, "Check how your budget is tracking", "check_budget"),
            ("Backup", "icons/backup.png", self.backup_screen, "Create a backup of your data", "backup"),
            ("Restore", "icons/restore.png", self.restore_screen, "Restore data from a backup", "restore"),
            ("Logout", "icons/logout.png", self.login_screen, "Sign out of the app", "logout")
        ]

        self.menu_buttons = []
        for text, icon_path, cmd, description, page_key in self.menu_items:
            icon = None
            if icon_path:
                img = Image.open(icon_path).resize((24, 24))
                icon = ImageTk.PhotoImage(img)

            btn_frame = tk.Frame(self.sidebar, bg=self.colors["sidebar"], height=42)
            btn_frame.pack(fill="x", pady=2)
            highlight = tk.Frame(btn_frame, bg=self.colors["accent"], width=0, height=42)
            highlight.pack(side="left", fill="y")
            btn = tk.Button(
                btn_frame,
                text=text if self.sidebar_expanded else "",
                image=icon,
                compound="left",
                bg=self.colors["sidebar"],
                fg=self.colors["sidebar_text"],
                anchor="w",
                bd=0,
                relief="flat",
                padx=12,
                activebackground=self.colors["hover"],
                activeforeground=self.colors["accent"],
                command=cmd
            )
            active = (self.current_page == page_key)
            btn.pack(side="left", fill="both", expand=True)
            self.apply_hover_effect(btn, highlight, active=active)
            self.set_button_state(btn, highlight, active)
            self.attach_tooltip(btn, description)
            btn.image = icon
            self.menu_buttons.append((btn_frame, btn, highlight))

    def toggle_sidebar(self):
        self.set_sidebar_state(not self.sidebar_expanded)

    # -----------------------------------------------------
    # LOGIN SCREEN (Frosted Cyan Glass)
    # -----------------------------------------------------
    def login_screen(self):
        self.current_page = "login"
        self.clear_window()

        panel_width = 520
        panel_height = 360
        frosted = create_frosted_panel(panel_width, panel_height)

        canvas = tk.Canvas(
            self.root,
            width=panel_width,
            height=panel_height,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        canvas.place(relx=0.5, rely=0.5, anchor="center")
        canvas.create_image(0, 0, anchor="nw", image=frosted)
        canvas.image = frosted

        tk.Label(
            canvas,
            text="Finance Manager",
            fg=self.colors["accent"],
            bg=self.colors["panel"],
            font=("Segoe UI", 24, "bold")
        ).place(x=150, y=24)

        tk.Label(
            canvas,
            text="Welcome back. Sign in to continue.",
            fg=self.colors["text"],
            bg=self.colors["panel"],
            font=("Segoe UI", 11)
        ).place(x=150, y=62)

        form_frame = tk.Frame(canvas, bg=self.colors["panel"], highlightthickness=0)
        form_frame.place(x=90, y=100, width=340, height=220)

        tk.Label(form_frame, text="Username", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        username = PlaceholderEntry(form_frame, placeholder="Enter username", font=("Segoe UI", 12))
        username.pack(fill="x", pady=(0, 10))

        tk.Label(form_frame, text="Password", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        password_frame = tk.Frame(form_frame, bg=self.colors["panel"], highlightthickness=0)
        password_frame.pack(fill="x")
        password = PasswordEntry(password_frame, font=("Segoe UI", 12))
        password.pack(side="left", fill="x", expand=True)
        eye_btn = tk.Button(
            password_frame,
            text="👁",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            command=password.toggle
        )
        eye_btn.pack(side="left", padx=(6, 0))

        ttk.Button(form_frame, text="Login", command=lambda: self.login(username.get(), password.get())).pack(pady=(14, 6))
        ttk.Button(form_frame, text="Create account", command=self.register_screen).pack()

        canvas.create_text(110, 335, text="Secure personal finance tracking", fill=self.colors["muted"], anchor="w", font=("Segoe UI", 9))

    # -----------------------------------------------------
    # REGISTER SCREEN
    # -----------------------------------------------------
    def register_screen(self):
        self.current_page = "register"
        self.clear_window()

        panel_width = 520
        panel_height = 380
        frosted = create_frosted_panel(panel_width, panel_height)

        canvas = tk.Canvas(
            self.root,
            width=panel_width,
            height=panel_height,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        canvas.place(relx=0.5, rely=0.5, anchor="center")
        canvas.create_image(0, 0, anchor="nw", image=frosted)
        canvas.image = frosted

        tk.Label(
            canvas,
            text="Create account",
            fg=self.colors["accent"],
            bg=self.colors["panel"],
            font=("Segoe UI", 24, "bold")
        ).place(x=155, y=24)

        tk.Label(
            canvas,
            text="Start tracking your money in a few seconds.",
            fg=self.colors["text"],
            bg=self.colors["panel"],
            font=("Segoe UI", 11)
        ).place(x=120, y=62)

        form_frame = tk.Frame(canvas, bg=self.colors["panel"], highlightthickness=0)
        form_frame.place(x=90, y=100, width=340, height=240)

        tk.Label(form_frame, text="Choose a username", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        username = PlaceholderEntry(form_frame, placeholder="Choose username", font=("Segoe UI", 12))
        username.pack(fill="x", pady=(0, 10))

        tk.Label(form_frame, text="Choose a password", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        password_frame = tk.Frame(form_frame, bg=self.colors["panel"], highlightthickness=0)
        password_frame.pack(fill="x")
        password = PasswordEntry(password_frame, font=("Segoe UI", 12))
        password.pack(side="left", fill="x", expand=True)
        eye_btn = tk.Button(
            password_frame,
            text="👁",
            bg=self.colors["panel"],
            fg=self.colors["accent"],
            command=password.toggle
        )
        eye_btn.pack(side="left", padx=(6, 0))

        ttk.Button(form_frame, text="Register", command=lambda: self.register(username.get(), password.get())).pack(pady=(14, 6))
        ttk.Button(form_frame, text="Back to login", command=self.login_screen).pack()

    # -----------------------------------------------------
    # LOGIN FUNCTION
    # -----------------------------------------------------
    def login(self, username, password):
        if login_user(username, password):
            self.logged_in_user = username
            self.last_login_time = datetime.datetime.now()
            self.dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    # -----------------------------------------------------
    # REGISTER FUNCTION
    # -----------------------------------------------------
    def register(self, username, password):
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        register_user(username, password)
        self.logged_in_user = username
        self.last_login_time = datetime.datetime.now()
        messagebox.showinfo("Success", "Registration successful. You are now logged in.")
        self.dashboard()

    # -----------------------------------------------------
    # DASHBOARD (Neon Glow Cards with REAL DATA)
    # -----------------------------------------------------
    def dashboard(self):
        self.current_page = "dashboard"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(
            content,
            text=f"Welcome, {self.logged_in_user}",
            fg=self.colors["accent"],
            bg=self.colors["surface"],
            font=("Segoe UI", 26, "bold")
        ).pack(pady=20)

        user_id = get_user_id(self.logged_in_user)
        income, expense, balance = get_user_totals(user_id)

        card_frame = tk.Frame(content, bg=self.colors["surface"])
        card_frame.pack(pady=20)

        card_data = [
            ("Total Income", income),
            ("Total Expense", expense),
            ("Balance", balance)
        ]

        latest_backup = self.get_backup_files(limit=1)
        backup_file = latest_backup[0][0] if latest_backup else None
        backup_card_text = self.get_latest_backup_summary()

        for title, value in card_data:
            card = tk.Frame(card_frame, bg=self.colors["panel"], width=230, height=120)
            card.pack(side="left", padx=16)
            card.configure(highlightbackground=self.colors["accent"], highlightthickness=2)
            card.bind("<Enter>", lambda e, c=card: c.configure(bg=self.colors["surface_alt"]))
            card.bind("<Leave>", lambda e, c=card: c.configure(bg=self.colors["panel"]))

            tk.Label(card, text=title, fg=self.colors["accent"], bg=self.colors["panel"], font=("Segoe UI", 15, "bold")).place(relx=0.5, rely=0.3, anchor="center")
            tk.Label(card, text=f"{value:.2f}", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 20, "bold")).place(relx=0.5, rely=0.7, anchor="center")

        backup_card = tk.Frame(card_frame, bg=self.colors["panel"], width=230, height=140, cursor="hand2")
        backup_card.pack(side="left", padx=16)
        backup_card.configure(highlightbackground=self.colors["accent"], highlightthickness=2)
        backup_card.bind("<Enter>", lambda e, c=backup_card: c.configure(bg=self.colors["surface_alt"]))
        backup_card.bind("<Leave>", lambda e, c=backup_card: c.configure(bg=self.colors["panel"]))
        if backup_file:
            backup_card.bind("<Button-1>", lambda e, path=backup_file: self.confirm_restore_screen(path))

        title_label = tk.Label(backup_card, text="Latest Backup", fg=self.colors["accent"], bg=self.colors["panel"], font=("Segoe UI", 15, "bold"))
        title_label.place(relx=0.5, rely=0.18, anchor="center")
        if backup_file:
            title_label.bind("<Button-1>", lambda e, path=backup_file: self.confirm_restore_screen(path))

        detail_label = tk.Label(backup_card, text=backup_card_text, fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10), wraplength=200, justify="center")
        detail_label.place(relx=0.5, rely=0.42, anchor="center")
        if backup_file:
            detail_label.bind("<Button-1>", lambda e, path=backup_file: self.confirm_restore_screen(path))

        button_state = "normal" if backup_file else "disabled"
        restore_latest_btn = ttk.Button(backup_card, text="Restore latest", width=18, command=lambda: self.restore_screen(backup_file) if backup_file else None, state=button_state)
        restore_latest_btn.place(relx=0.5, rely=0.76, anchor="center")

        if not backup_file:
            warning_label = tk.Label(backup_card, text="No backup available yet", fg=self.colors["danger"], bg=self.colors["panel"], font=("Segoe UI", 8, "bold"))
            warning_label.place(relx=0.5, rely=0.92, anchor="center")

        budgets_frame = tk.Frame(content, bg=self.colors["surface"])
        budgets_frame.pack(pady=20)
        tk.Label(budgets_frame, text="Budgets", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 8))

        month = datetime.date.today().strftime("%Y-%m")
        budgets = list_budgets(user_id, month)

        for b in budgets:
            _, category, limit, mon = b
            status = get_budget_progress(user_id, category, mon) or {"limit": limit, "spent": 0, "percent": 0}
            frame = tk.Frame(budgets_frame, bg=self.colors["surface_alt"], pady=6, padx=8)
            frame.pack(fill="x", padx=10, pady=6)
            tk.Label(frame, text=f"{category}", fg=self.colors["accent"], bg=self.colors["surface_alt"], font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(frame, text=f"{status['spent']:.2f}/{status['limit']:.2f}", fg=self.colors["text"], bg=self.colors["surface_alt"]).pack(side="left", padx=10)
            pb = ttk.Progressbar(frame, length=220, value=min(status.get("percent", 0), 100))
            pb.pack(side="right")

        analytics_frame = tk.Frame(content, bg=self.colors["surface"])
        analytics_frame.pack(pady=16)
        ttk.Button(analytics_frame, text="Show Monthly Trend", command=self.show_monthly_trend_dialog).pack(side="left", padx=6)
        ttk.Button(analytics_frame, text="Show Category Breakdown", command=self.show_category_breakdown_dialog).pack(side="left", padx=6)

        self.build_status_bar()

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def get_backup_files(self, limit=5):
        try:
            files = [f for f in os.listdir(BASE_DIR) if f.endswith('.db') and 'backup' in f.lower()]
            files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(BASE_DIR, f)), reverse=True)
            return [
                (
                    f,
                    datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE_DIR, f))).strftime('%Y-%m-%d %H:%M'),
                    self.format_size(os.path.getsize(os.path.join(BASE_DIR, f)))
                )
                for f in files[:limit]
            ]
        except Exception:
            return []

    def get_latest_backup_summary(self):
        backups = self.get_backup_files(limit=1)
        if not backups:
            return "No backup found"

        latest, modified, size = backups[0]
        return f"{latest}\n{modified} • {size}"

    def build_status_bar(self):
        # remove existing if any
        if hasattr(self, 'status_bar') and self.status_bar:
            try:
                self.status_bar.destroy()
            except Exception:
                pass

        self.status_bar = tk.Frame(self.root, bg=self.colors["sidebar"], height=28)
        self.status_bar.pack(side="bottom", fill="x")
        user_text = f"User: {self.logged_in_user}" if self.logged_in_user else "Not logged in"
        time_text = f"Last login: {self.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_time else 'N/A'}"
        tk.Label(self.status_bar, text=user_text, fg=self.colors["sidebar_text"], bg=self.colors["sidebar"]).pack(side="left", padx=8)
        tk.Label(self.status_bar, text=time_text, fg=self.colors["accent"], bg=self.colors["sidebar"]).pack(side="right", padx=8)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        if self.theme == "light":
            self.colors = {
                **APP_COLORS,
                "bg": "#f7f9ff",
                "surface": "#ffffff",
                "surface_alt": "#eef4ff",
                "panel": "#eef4ff",
                "border": "#d7e2f0",
                "sidebar": "#0f172a",
                "text": "#14213d",
                "muted": "#6b7280",
                "sidebar_text": "#f7fbff"
            }
        else:
            self.colors = APP_COLORS.copy()
        self.apply_global_styles()
        if self.logged_in_user:
            self.dashboard()
        else:
            self.login_screen()

    def show_monthly_trend_dialog(self):
        user_id = get_user_id(self.logged_in_user)
        labels, incomes, expenses = monthly_trend(user_id, months=6)

        plt.figure(figsize=(6, 3))
        plt.plot(labels, incomes, label="Income", marker='o', color="#00E5FF")
        plt.plot(labels, expenses, label="Expense", marker='o', color="#FF6B6B")
        plt.title("Monthly Income vs Expense")
        plt.xlabel("Month")
        plt.ylabel("Amount")
        plt.legend()
        plt.tight_layout()
        # save to file in working directory
        out = "monthly_trend.png"
        plt.savefig(out)
        plt.show()
        messagebox.showinfo("Saved", f"Monthly trend chart saved to {out}")

    def show_category_breakdown_dialog(self):
        user_id = get_user_id(self.logged_in_user)
        import datetime
        month = datetime.date.today().strftime("%Y-%m")
        data = category_breakdown(user_id, month)
        labels = list(data.keys())
        values = list(data.values())
        if not labels:
            messagebox.showinfo("No data", "No transactions for current month.")
            return

        plt.figure(figsize=(5, 5))
        plt.pie(values, labels=labels, autopct="%.1f%%")
        plt.title(f"Category breakdown ({month})")
        out = "category_breakdown.png"
        plt.savefig(out)
        plt.show()
        messagebox.showinfo("Saved", f"Category breakdown saved to {out}")

    # -----------------------------------------------------
    # PROFILE SCREEN
    # -----------------------------------------------------
    def profile_screen(self):
        self.current_page = "profile"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(
            content,
            text="Profile",
            fg=self.colors["accent"],
            bg=self.colors["surface"],
            font=("Segoe UI", 24, "bold")
        ).pack(pady=20)

        user_id = get_user_id(self.logged_in_user)

        # Image container
        img_frame = tk.Frame(content, bg=self.colors["surface"])
        img_frame.pack(pady=10)

        img_path = get_profile_pic(user_id) if user_id else None

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert("RGBA").resize((120, 120))
                mask = Image.new("L", (120, 120), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 120, 120), fill=255)
                img.putalpha(mask)
                photo = ImageTk.PhotoImage(img)
            except Exception:
                photo = None
        else:
            photo = None

        if photo:
            lbl = tk.Label(img_frame, image=photo, bg="#0f0f0f")
            lbl.image = photo
            lbl.pack()
        else:
            placeholder = tk.Canvas(img_frame, width=120, height=120, bg=self.colors["surface"], highlightthickness=0)
            placeholder.create_oval(5, 5, 115, 115, fill=self.colors["panel"], outline=self.colors["accent"], width=4)
            initials = (self.logged_in_user[:1].upper() if self.logged_in_user else "U")
            placeholder.create_text(60, 60, text=initials, fill="white", font=("Segoe UI", 36, "bold"))
            placeholder.pack()

        # Username
        tk.Label(content, text=f"{self.logged_in_user}", fg=self.colors["text"], bg=self.colors["surface"], font=("Segoe UI", 16)).pack(pady=8)

        ttk.Button(content, text="Upload Photo", command=lambda: self.upload_profile_photo(user_id)).pack(pady=8)
        ttk.Button(content, text="Back", command=self.dashboard).pack(pady=8)

    def upload_profile_photo(self, user_id):
        if not user_id:
            messagebox.showerror("Error", "No logged-in user found.")
            return

        path = filedialog.askopenfilename(title="Select profile image", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
        if not path:
            return

        # Save path in DB and refresh profile screen
        try:
            update_profile_pic(user_id, path)
            messagebox.showinfo("Success", "Profile photo updated")
            self.profile_screen()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update photo: {e}")

    # -----------------------------------------------------
    # ADD TRANSACTION
    # -----------------------------------------------------
    def add_transaction_screen(self):
        self.current_page = "add_transaction"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 12))
        tk.Label(header, text="Add Transaction", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Log income or expenses with a cleaner, faster form.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        form_card = tk.Frame(content, bg=self.colors["panel"], highlightbackground=self.colors["accent"], highlightthickness=2, padx=18, pady=18)
        form_card.pack(fill="both", expand=True)

        fields = ["Amount", "Category", "Type (income/expense)", "Date (YYYY-MM-DD)"]
        entries = {}

        for field in fields:
            row = tk.Frame(form_card, bg=self.colors["panel"])
            row.pack(fill="x", pady=8)
            tk.Label(row, text=field, fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))

            if field == "Date (YYYY-MM-DD)":
                entry = self.create_date_picker(row, width=24)
            elif field == "Type (income/expense)":
                entry = ttk.Combobox(row, values=["income", "expense"], state="readonly", width=22)
                entry.current(1)
            else:
                entry = ttk.Entry(row, width=24)

            entry.pack(fill="x")
            entries[field] = entry

        hint = tk.Label(form_card, text="Tip: use clear categories like Salary, Food, Travel, or Rent.", fg=self.colors["muted"], bg=self.colors["panel"], font=("Segoe UI", 9))
        hint.pack(anchor="w", pady=(8, 0))

        buttons = tk.Frame(form_card, bg=self.colors["panel"])
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="Add Transaction", command=lambda: self.add_transaction(entries)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Back", command=self.dashboard).pack(side="left")

    def add_transaction(self, entries):
        # Validate amount
        amount_str = entries["Amount"].get()
        try:
            amount = float(amount_str)
        except Exception:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")
            return

        category = entries["Category"].get()
        t_type = entries["Type (income/expense)"].get()
        date = entries["Date (YYYY-MM-DD)"].get()

        user_id = get_user_id(self.logged_in_user)
        add_transaction(user_id, amount, category, t_type, date)
        # Check budget for this category/month
        month = date[:7]
        bstatus = get_budget_progress(user_id, category, month)
        if bstatus and bstatus.get("exceeded"):
            messagebox.showwarning("Budget Exceeded", f"You exceeded the budget for {category}: {bstatus['spent']}/{bstatus['limit']}")
        else:
            messagebox.showinfo("Success", "Transaction added")
        self.dashboard()

    # -----------------------------------------------------
    # VIEW TRANSACTIONS
    # -----------------------------------------------------
    def view_transactions_screen(self):
        self.current_page = "view_transactions"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 10))
        tk.Label(header, text="Transactions", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Browse, search, and update your latest entries.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        # Filters
        filter_frame = tk.Frame(content, bg=self.colors["surface"], padx=8, pady=8)
        filter_frame.pack(fill="x", pady=10)

        tk.Label(filter_frame, text="Category:", fg=self.colors["text"], bg=self.colors["surface"]).grid(row=0, column=0, padx=4)
        cat_entry = ttk.Entry(filter_frame)
        cat_entry.grid(row=0, column=1, padx=4)

        tk.Label(filter_frame, text="From:", fg=self.colors["text"], bg=self.colors["surface"]).grid(row=0, column=2, padx=4)
        from_entry = self.create_date_picker(filter_frame, width=12)
        from_entry.grid(row=0, column=3, padx=4)

        tk.Label(filter_frame, text="To:", fg=self.colors["text"], bg=self.colors["surface"]).grid(row=0, column=4, padx=4)
        to_entry = self.create_date_picker(filter_frame, width=12)
        to_entry.grid(row=0, column=5, padx=4)

        user_id = get_user_id(self.logged_in_user)

        def do_search():
            category = cat_entry.get().strip() or None
            start = from_entry.get().strip() or None
            end = to_entry.get().strip() or None
            rows = search_transactions(user_id, category=category, start_date=start, end_date=end)
            for i in tree.get_children():
                tree.delete(i)
            for r in rows:
                tag = "income" if str(r[3]).lower() == "income" else "expense"
                tree.insert("", "end", values=r, tags=(tag,))

        ttk.Button(filter_frame, text="Search", command=do_search).grid(row=0, column=6, padx=6)
        ttk.Button(filter_frame, text="Reset", command=lambda: load_all()).grid(row=0, column=7, padx=6)

        tree = ttk.Treeview(
            content,
            columns=("ID", "Amount", "Category", "Type", "Date"),
            show="headings",
            selectmode="browse",
            style="Modern.Treeview"
        )

        for col in ("ID", "Amount", "Category", "Type", "Date"):
            tree.heading(col, text=col)

        income_bg = "#d8f3ff" if self.theme == "light" else "#0f2f2f"
        expense_bg = "#ffd8d8" if self.theme == "light" else "#2f1717"
        income_fg = "#14213d" if self.theme == "light" else self.colors["text"]
        expense_fg = "#14213d" if self.theme == "light" else self.colors["text"]

        tree.tag_configure("income", background=income_bg, foreground=income_fg)
        tree.tag_configure("expense", background=expense_bg, foreground=expense_fg)

        tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Sorting support
        def sort_column(col, reverse=False):
            data = [(tree.set(k, col), k) for k in tree.get_children('')]
            try:
                data.sort(key=lambda t: float(t[0]), reverse=reverse)
            except Exception:
                data.sort(key=lambda t: t[0], reverse=reverse)
            for index, (val, k) in enumerate(data):
                tree.move(k, '', index)
            tree.heading(col, command=lambda: sort_column(col, not reverse))

        for col in ("ID", "Amount", "Category", "Type", "Date"):
            tree.heading(col, text=col, command=lambda _col=col: sort_column(_col, False))

        # Action buttons
        action_frame = tk.Frame(content, bg=self.colors["surface"])
        action_frame.pack(pady=8)

        def load_all():
            for i in tree.get_children():
                tree.delete(i)
            for t in view_transactions(user_id):
                tag = "income" if str(t[3]).lower() == "income" else "expense"
                tree.insert("", "end", values=t, tags=(tag,))

        def edit_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Please select a transaction to edit")
                return
            vals = tree.item(sel[0])['values']
            t_id = vals[0]

            # open edit dialog
            dlg = tk.Toplevel(self.root)
            dlg.configure(bg=self.colors["surface"])
            dlg.title("Edit Transaction")

            tk.Label(dlg, text="Amount").grid(row=0, column=0)
            amt_e = ttk.Entry(dlg)
            amt_e.grid(row=0, column=1)
            amt_e.insert(0, vals[1])

            tk.Label(dlg, text="Category").grid(row=1, column=0)
            cat_e = ttk.Entry(dlg)
            cat_e.grid(row=1, column=1)
            cat_e.insert(0, vals[2])

            tk.Label(dlg, text="Type").grid(row=2, column=0)
            type_e = ttk.Entry(dlg)
            type_e.grid(row=2, column=1)
            type_e.insert(0, vals[3])

            tk.Label(dlg, text="Date").grid(row=3, column=0)
            date_e = self.create_date_picker(dlg)
            date_e.grid(row=3, column=1)
            date_e.set_date(vals[4])

            def do_update():
                update_transaction(t_id, amount=float(amt_e.get()), category=cat_e.get(), t_type=type_e.get(), date=date_e.get())
                dlg.destroy()
                load_all()

            def do_delete():
                delete_transaction(t_id)
                dlg.destroy()
                load_all()

            ttk.Button(dlg, text="Update", command=do_update).grid(row=4, column=0)
            ttk.Button(dlg, text="Delete", command=do_delete).grid(row=4, column=1)

        ttk.Button(action_frame, text="Edit Selected", command=edit_selected).pack(side="left", padx=6)
        ttk.Button(action_frame, text="Refresh", command=load_all).pack(side="left", padx=6)

        user_id = get_user_id(self.logged_in_user)
        load_all()

    # -----------------------------------------------------
    # MONTHLY REPORT
    # -----------------------------------------------------
    def monthly_report_screen(self):
        self.current_page = "monthly_report"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(content, text="Monthly Report", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(pady=20)
        tk.Label(content, text="Choose a date to derive the month", fg=self.colors["muted"], bg=self.colors["surface"]).pack()
        entry = self.create_date_picker(content)
        entry.pack(pady=10)

        ttk.Button(content, text="Generate", command=lambda: self.show_monthly_report(entry.get())).pack(pady=10)
        ttk.Button(content, text="Back", command=self.dashboard).pack(pady=6)

    def show_monthly_report(self, month):
        user_id = get_user_id(self.logged_in_user)
        data = monthly_report(user_id, month)
        income = data.get("income", 0)
        expense = data.get("expenses", data.get("expense", 0))
        if income + expense == 0:
            messagebox.showinfo("No data", "No transactions for this month.")
            return

        chart_data = {
            "labels": ["Income", "Expense"],
            "values": [income, expense],
            "colors": ["#00E5FF", "#FF6B6B"],
            "title": f"Monthly report for {month}",
            "savings": income - expense,
        }

        self.open_report_dialog(chart_data)

    # -----------------------------------------------------
    # YEARLY REPORT
    # -----------------------------------------------------
    def yearly_report_screen(self):
        self.current_page = "yearly_report"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(content, text="Yearly Report", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(pady=20)
        tk.Label(content, text="Choose a date to derive the year", fg=self.colors["muted"], bg=self.colors["surface"]).pack()
        entry = self.create_date_picker(content)
        entry.pack(pady=10)

        ttk.Button(content, text="Generate", command=lambda: self.show_yearly_report(entry.get())).pack(pady=10)
        ttk.Button(content, text="Back", command=self.dashboard).pack(pady=6)

    def show_yearly_report(self, year):
        user_id = get_user_id(self.logged_in_user)
        data = yearly_report(user_id, year)
        income = data.get("income", 0)
        expense = data.get("expenses", data.get("expense", 0))
        if income + expense == 0:
            messagebox.showinfo("No data", "No transactions for this year.")
            return

        chart_data = {
            "labels": ["Income", "Expense"],
            "values": [income, expense],
            "colors": ["#00E5FF", "#FF6B6B"],
            "title": f"Yearly report for {year}",
            "savings": income - expense,
        }

        self.open_report_dialog(chart_data)

    def open_report_dialog(self, chart_data):
        dlg = tk.Toplevel(self.root)
        dlg.title(chart_data["title"])
        dlg.configure(bg=self.colors["surface"])
        dlg.geometry("520x420")

        tk.Label(dlg, text=chart_data["title"], fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 16, "bold")).pack(pady=(16, 8))

        summary = tk.Frame(dlg, bg=self.colors["surface"])
        summary.pack(pady=8)
        tk.Label(summary, text=f"Income: {chart_data['values'][0]:.2f}", fg=self.colors["text"], bg=self.colors["surface"]).pack(side="left", padx=10)
        tk.Label(summary, text=f"Expense: {chart_data['values'][1]:.2f}", fg=self.colors["text"], bg=self.colors["surface"]).pack(side="left", padx=10)
        tk.Label(summary, text=f"Savings: {chart_data['savings']:.2f}", fg=self.colors["success"], bg=self.colors["surface"]).pack(side="left", padx=10)

        canvas = tk.Canvas(dlg, width=280, height=220, bg=self.colors["surface"], highlightthickness=0)
        canvas.pack(pady=12)
        canvas.create_oval(20, 20, 260, 220, fill=self.colors["panel"], outline=self.colors["accent"], width=2)
        canvas.create_text(140, 110, text=f"{chart_data['values'][0]:.0f}\nvs\n{chart_data['values'][1]:.0f}", fill=self.colors["text"], font=("Segoe UI", 12, "bold"), justify="center")

        ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=8)

    # -----------------------------------------------------
    # SET BUDGET
    # -----------------------------------------------------
    def set_budget_screen(self):
        self.current_page = "set_budget"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 12))
        tk.Label(header, text="Set Budget", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Plan your spending by category and month.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        form_card = tk.Frame(content, bg=self.colors["panel"], highlightbackground=self.colors["accent"], highlightthickness=2, padx=18, pady=18)
        form_card.pack(fill="both", expand=True)

        fields = ["Category", "Budget Limit", "Month (YYYY-MM)"]
        entries = {}

        for field in fields:
            row = tk.Frame(form_card, bg=self.colors["panel"])
            row.pack(fill="x", pady=8)
            tk.Label(row, text=field, fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))
            if field == "Month (YYYY-MM)":
                entry = self.create_date_picker(row, width=24)
            else:
                entry = ttk.Entry(row, width=24)
            entry.pack(fill="x")
            entries[field] = entry

        buttons = tk.Frame(form_card, bg=self.colors["panel"])
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="Save Budget", command=lambda: self.set_budget(entries)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Back", command=self.dashboard).pack(side="left")

    def set_budget(self, entries):
        category = entries["Category"].get().strip()
        limit_str = entries["Budget Limit"].get().strip()
        month = entries["Month (YYYY-MM)"].get().strip()

        if not category or not limit_str or not month:
            messagebox.showwarning("Missing fields", "Please fill in all budget fields.")
            return

        try:
            limit = float(limit_str)
        except ValueError:
            messagebox.showerror("Invalid amount", "Budget limit must be a valid number.")
            return

        month = self.normalize_month_value(month)

        user_id = get_user_id(self.logged_in_user)
        set_budget(user_id, category, limit, month)
        messagebox.showinfo("Success", "Budget set")
        self.dashboard()

    # -----------------------------------------------------
    # CHECK BUDGET
    # -----------------------------------------------------
    def check_budget_screen(self):
        self.current_page = "check_budget"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 12))
        tk.Label(header, text="Check Budget", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Review current budget health and overspending.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        form_card = tk.Frame(content, bg=self.colors["panel"], highlightbackground=self.colors["accent"], highlightthickness=2, padx=18, pady=18)
        form_card.pack(fill="both", expand=True)

        tk.Label(form_card, text="Category", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        category = ttk.Entry(form_card, width=24)
        category.pack(fill="x")

        tk.Label(form_card, text="Month", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
        month = self.create_date_picker(form_card, width=24)
        month.pack(fill="x")

        buttons = tk.Frame(form_card, bg=self.colors["panel"])
        buttons.pack(fill="x", pady=(16, 0))
        ttk.Button(buttons, text="Check", command=lambda: self.show_budget(category.get(), self.normalize_month_value(month.get()))).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Back", command=self.dashboard).pack(side="left")

    def show_budget(self, category, month):
        user_id = get_user_id(self.logged_in_user)
        result = check_budget(user_id, category, self.normalize_month_value(month))
        if not result:
            messagebox.showinfo("Budget Status", f"No budget found for {category or 'this category'} in {month}.")
            return

        status_text = (
            f"Category: {category}\n"
            f"Limit: {result['limit']:.2f}\n"
            f"Spent: {result['spent']:.2f}\n"
            f"Percent used: {result['percent']:.1f}%\n"
            f"Status: {'Exceeded' if result['exceeded'] else 'On track'}"
        )
        messagebox.showinfo("Budget Status", status_text)

    # -----------------------------------------------------
    # BACKUP & RESTORE
    # -----------------------------------------------------
    def backup_screen(self):
        self.current_page = "backup"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 12))
        tk.Label(header, text="Backup Database", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Create a safe copy of your file so your data is always protected.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        default_backup = f"finance_app_backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.db"
        self.backup_path = tk.StringVar(value=default_backup)
        form_card = tk.Frame(content, bg=self.colors["panel"], highlightbackground=self.colors["accent"], highlightthickness=2, padx=18, pady=18)
        form_card.pack(fill="both", expand=True)

        tk.Label(form_card, text="Backup file", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))
        tk.Entry(form_card, textvariable=self.backup_path, width=36).pack(fill="x", pady=(0, 10))

        button_bar = tk.Frame(form_card, bg=self.colors["panel"])
        button_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(button_bar, text="Choose location", command=self.select_backup_location).pack(side="left", padx=(0, 8))
        ttk.Button(button_bar, text="Create Backup", command=self.backup_db).pack(side="left")
        ttk.Button(button_bar, text="Back", command=self.dashboard).pack(side="left", padx=(8, 0))

    def restore_screen(self, restore_file=None):
        self.current_page = "restore"
        self.clear_window()
        self.build_sidebar()

        content = self.create_panel(self.root)
        content.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(content, bg=self.colors["surface"])
        header.pack(fill="x", pady=(16, 12))
        tk.Label(header, text="Restore Database", fg=self.colors["accent"], bg=self.colors["surface"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text="Restore data from a backup copy if you need to recover your records.", fg=self.colors["muted"], bg=self.colors["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        self.restore_path = tk.StringVar(value=restore_file or "finance_app_backup.db")
        form_card = tk.Frame(content, bg=self.colors["panel"], highlightbackground=self.colors["accent"], highlightthickness=2, padx=18, pady=18)
        form_card.pack(fill="both", expand=True)

        tk.Label(form_card, text="Backup file to restore", fg=self.colors["text"], bg=self.colors["panel"], font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))
        tk.Entry(form_card, textvariable=self.restore_path, width=36).pack(fill="x", pady=(0, 10))

        selected_label = tk.Label(form_card, text=f"Selected backup: {self.restore_path.get()}", fg=self.colors["muted"], bg=self.colors["panel"], font=("Segoe UI", 9, "italic"), anchor="w")
        selected_label.pack(anchor="w", pady=(0, 10))

        recent_frame = tk.Frame(form_card, bg=self.colors["panel"])
        recent_frame.pack(fill="both", expand=True, pady=(10, 0))
        tk.Label(recent_frame, text="Recent backups", fg=self.colors["accent"], bg=self.colors["panel"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        recent_list = tk.Listbox(recent_frame, height=4, bg=self.colors["surface"], fg=self.colors["text"], selectbackground=self.colors["accent"], selectforeground=self.colors["bg"], activestyle="none")
        recent_list.pack(fill="x", pady=(0, 10))

        backup_files = self.get_backup_files(limit=5)
        self.recent_backup_files = [filename for filename, _, _ in backup_files]

        selected_index = None
        if backup_files:
            for idx, (filename, modified, size) in enumerate(backup_files):
                recent_list.insert("end", f"{filename}   ({modified}, {size})")
                if restore_file and filename == restore_file:
                    selected_index = idx
            if selected_index is None:
                selected_index = 0
        else:
            recent_list.insert("end", "No recent backups found")
            recent_list.config(state="disabled")

        def select_recent(event=None):
            selection = recent_list.curselection()
            if selection and selection[0] < len(self.recent_backup_files):
                self.restore_path.set(self.recent_backup_files[selection[0]])
                selected_label.config(text=f"Selected backup: {self.restore_path.get()}")

        recent_list.bind("<<ListboxSelect>>", select_recent)
        recent_list.bind("<Double-Button-1>", lambda event: self.restore_db())

        if selected_index is not None and backup_files:
            recent_list.selection_set(selected_index)
            recent_list.activate(selected_index)
            recent_list.see(selected_index)
            self.restore_path.set(self.recent_backup_files[selected_index])

        button_bar = tk.Frame(form_card, bg=self.colors["panel"])
        button_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(button_bar, text="Choose file", command=self.select_restore_location).pack(side="left", padx=(0, 8))
        ttk.Button(button_bar, text="Restore Backup", command=self.restore_db).pack(side="left")
        ttk.Button(button_bar, text="Back", command=self.dashboard).pack(side="left", padx=(8, 0))

    def confirm_restore_screen(self, restore_file):
        if not restore_file:
            messagebox.showwarning("No backup selected", "There is no latest backup to restore.")
            return

        confirm = messagebox.askyesno(
            "Confirm restore",
            f"A restore session will open with the latest backup selected:\n{restore_file}\n\nContinue to restore screen?"
        )
        if confirm:
            self.restore_screen(restore_file)

    def select_backup_location(self):
        path = filedialog.asksaveasfilename(
            title="Save backup as",
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*")],
            initialfile=self.backup_path.get()
        )
        if path:
            self.backup_path.set(path)

    def select_restore_location(self):
        path = filedialog.askopenfilename(
            title="Select backup file",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*")]
        )
        if path:
            self.restore_path.set(path)

    def backup_db(self):
        backup_file = self.backup_path.get().strip()
        if not backup_file:
            messagebox.showwarning("No file selected", "Please enter a backup filename first.")
            return

        success = backup_database(backup_file)
        if success:
            messagebox.showinfo("Success", f"Backup created at {backup_file}")
        else:
            messagebox.showerror("Error", f"Backup failed. Check the destination path and permissions.")

    def restore_db(self):
        backup_file = self.restore_path.get().strip()
        if not backup_file:
            messagebox.showwarning("No file selected", "Please choose a backup file first.")
            return

        backup_file = backup_file if os.path.isabs(backup_file) else os.path.join(BASE_DIR, backup_file)
        if not os.path.exists(backup_file):
            messagebox.showerror("File missing", f"The backup file {backup_file} does not exist.")
            return

        confirm = messagebox.askyesno(
            "Confirm restore",
            f"This will overwrite your current database with {backup_file}.\nDo you want to continue?"
        )
        if not confirm:
            return

        success, fallback_file = restore_database(backup_file)
        if success:
            msg = f"Database restored from {backup_file}."
            if fallback_file:
                msg += f"\nA pre-restore copy was saved as {fallback_file}."
            messagebox.showinfo("Success", msg)
            self.dashboard()
        else:
            messagebox.showerror("Error", "Restore failed. Please check the backup file and try again.")

    # -----------------------------------------------------
    # CLEAR WINDOW
    # -----------------------------------------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------
root = tk.Tk()
app = FinanceApp(root)
root.mainloop()
