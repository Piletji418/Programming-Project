"""
Tkinter GUI for the Smart Campus Resource Booking System.
Provides role-based interfaces for Lecturers, Campus Administrators and System Operators.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from models import create_user_from_dict, User, Campus


class LoginWindow:
    """Login and registration window."""

    def __init__(self, root: tk.Tk, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("Smart Campus Resource Booking System - Login")
        self.root.geometry("420x380")
        self.root.resizable(False, False)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 420, 380
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Smart Campus Booking", style="Title.TLabel").pack(pady=(0, 5))
        ttk.Label(main, text="Richfield Graduate Institution", font=("Segoe UI", 9)).pack(pady=(0, 15))

        form = ttk.LabelFrame(main, text="Login", padding=15)
        form.pack(fill=tk.X, pady=5)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var, width=28).grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.password_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.password_var, show="*", width=28).grid(row=1, column=1, pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Login", command=self._login, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Register Lecturer", command=self._show_register, width=16).pack(side=tk.LEFT, padx=5)

        # Demo accounts info
        info = ttk.LabelFrame(main, text="Demo Accounts (password shown)", padding=10)
        info.pack(fill=tk.X, pady=10)
        demo_text = (
            "lecturer1 / pass123  (Lecturer - JHB)\n"
            "admin_jhb / admin123  (Admin - Johannesburg)\n"
            "operator1 / ops123  (System Operator)"
        )
        ttk.Label(info, text=demo_text, font=("Consolas", 9), justify=tk.LEFT).pack(anchor=tk.W)

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter username and password.")
            return
        user_data = db.authenticate_user(username, password)
        if user_data:
            user = create_user_from_dict(user_data)
            self.on_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def _show_register(self):
        reg = tk.Toplevel(self.root)
        reg.title("Register New Lecturer")
        reg.geometry("380x320")
        reg.transient(self.root)
        reg.grab_set()

        frame = ttk.Frame(reg, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=4)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=4)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=4)
        uname_var = tk.StringVar()
        ttk.Entry(frame, textvariable=uname_var, width=30).grid(row=1, column=1, pady=4)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=4)
        pwd_var = tk.StringVar()
        ttk.Entry(frame, textvariable=pwd_var, show="*", width=30).grid(row=2, column=1, pady=4)

        ttk.Label(frame, text="Campus:").grid(row=3, column=0, sticky=tk.W, pady=4)
        campuses = db.get_all_campuses()
        campus_names = [c["name"] for c in campuses]
        campus_var = tk.StringVar(value=campus_names[0] if campus_names else "")
        ttk.Combobox(frame, textvariable=campus_var, values=campus_names, state="readonly", width=28).grid(row=3, column=1, pady=4)

        def do_register():
            name = name_var.get().strip()
            uname = uname_var.get().strip()
            pwd = pwd_var.get()
            cname = campus_var.get()
            cid = next((c["campus_id"] for c in campuses if c["name"] == cname), None)
            if not cid:
                messagebox.showerror("Error", "Please select a campus.", parent=reg)
                return
            ok, msg = db.register_lecturer(uname, pwd, name, cid)
            if ok:
                messagebox.showinfo("Success", msg, parent=reg)
                reg.destroy()
            else:
                messagebox.showerror("Registration Failed", msg, parent=reg)

        ttk.Button(frame, text="Register", command=do_register).grid(row=4, column=0, columnspan=2, pady=15)


class MainApplication:
    """Main application window with role-based dashboards."""

    def __init__(self, root: tk.Tk, user: User):
        self.root = root
        self.user = user
        self.current_campus_id: Optional[int] = user.campus_id
        self.campuses = {c["campus_id"]: c for c in db.get_all_campuses()}

        self.root.title(f"Smart Campus Booking - {user.full_name} ({user.role.title()})")
        self.root.geometry("980x640")
        self.root.minsize(800, 550)

        self._build_menu()
        self._build_header()
        self._build_notebook()
        self._refresh_campus_label()

        # Default to user's campus or first available
        if self.current_campus_id is None and self.campuses:
            self.current_campus_id = next(iter(self.campuses))
            self._refresh_campus_label()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Logout", command=self._logout)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        if self.user.role in ("admin", "operator", "lecturer"):
            campus_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Campus", menu=campus_menu)
            for cid, c in self.campuses.items():
                # Admins restricted to own campus
                if self.user.role == "admin" and cid != self.user.campus_id:
                    continue
                campus_menu.add_command(
                    label=c["name"],
                    command=lambda i=cid: self._select_campus(i)
                )

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(10, 8))
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"Logged in as: {self.user.full_name}",
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.campus_label = ttk.Label(header, text="", font=("Segoe UI", 10))
        self.campus_label.pack(side=tk.RIGHT)
        self.policy_label = ttk.Label(header, text="", font=("Segoe UI", 9), foreground="#555")
        self.policy_label.pack(side=tk.RIGHT, padx=15)

    def _refresh_campus_label(self):
        if self.current_campus_id and self.current_campus_id in self.campuses:
            c = self.campuses[self.current_campus_id]
            self.campus_label.config(text=f"Active Campus: {c['name']}")
            self.policy_label.config(
                text=f"Policy: Max {c['max_duration_hours']}h | "
                     f"{c['open_hour']:02d}:00-{c['close_hour']:02d}:00"
            )
        else:
            self.campus_label.config(text="No campus selected")
            self.policy_label.config(text="")

    def _select_campus(self, campus_id: int):
        if self.user.role == "admin" and campus_id != self.user.campus_id:
            messagebox.showwarning("Access Denied", "You can only manage your assigned campus.")
            return
        self.current_campus_id = campus_id
        self._refresh_campus_label()
        # Refresh relevant tabs
        if hasattr(self, "resources_tree"):
            self._load_resources()
        if hasattr(self, "bookings_tree"):
            self._load_bookings()
        messagebox.showinfo("Campus Selected", f"Now working with: {self.campuses[campus_id]['name']}")

    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Common: Resources tab
        self.resources_frame = ttk.Frame(self.nb, padding=8)
        self.nb.add(self.resources_frame, text="Resources")
        self._build_resources_tab()

        # Role-specific tabs
        if self.user.role == "lecturer":
            self.book_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.book_frame, text="Make Booking")
            self._build_booking_tab()

            self.mybook_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.mybook_frame, text="My Bookings")
            self._build_my_bookings_tab()

        if self.user.role in ("admin", "operator"):
            self.manage_res_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.manage_res_frame, text="Manage Resources")
            self._build_manage_resources_tab()

            self.allbook_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.allbook_frame, text="Campus Bookings")
            self._build_campus_bookings_tab()

        if self.user.role == "operator":
            self.report_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.report_frame, text="Reports")
            self._build_reports_tab()

        if self.user.role == "admin":
            self.report_frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(self.report_frame, text="Campus Report")
            self._build_admin_report_tab()

    # -------------------- Resources Tab (view) --------------------
    def _build_resources_tab(self):
        toolbar = ttk.Frame(self.resources_frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(toolbar, text="Refresh", command=self._load_resources).pack(side=tk.LEFT)

        cols = ("ID", "Name", "Type", "Capacity", "Description", "Status")
        self.resources_tree = ttk.Treeview(self.resources_frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.resources_tree.heading(c, text=c)
            self.resources_tree.column(c, width=120 if c != "Description" else 220)
        self.resources_tree.column("ID", width=50)
        self.resources_tree.pack(fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(self.resources_tree, orient=tk.VERTICAL, command=self.resources_tree.yview)
        self.resources_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_resources()

    def _load_resources(self):
        for i in self.resources_tree.get_children():
            self.resources_tree.delete(i)
        if not self.current_campus_id:
            return
        resources = db.get_resources_by_campus(self.current_campus_id, active_only=False)
        for r in resources:
            status = "Active" if r["is_active"] else "Inactive"
            self.resources_tree.insert("", tk.END, values=(
                r["resource_id"], r["name"], r["resource_type"],
                r["capacity"], r.get("description", ""), status
            ))

    # -------------------- Lecturer: Make Booking --------------------
    def _build_booking_tab(self):
        form = ttk.LabelFrame(self.book_frame, text="New Booking", padding=12)
        form.pack(fill=tk.X, pady=5)

        ttk.Label(form, text="Resource:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.book_resource_var = tk.StringVar()
        self.book_resource_combo = ttk.Combobox(form, textvariable=self.book_resource_var, state="readonly", width=40)
        self.book_resource_combo.grid(row=0, column=1, pady=4, sticky=tk.W)
        self._populate_resource_combo()

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.book_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.book_date_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=4)

        ttk.Label(form, text="Start Time (HH:MM):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.book_time_var = tk.StringVar(value="09:00")
        ttk.Entry(form, textvariable=self.book_time_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=4)

        ttk.Label(form, text="Duration (hours):").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.book_duration_var = tk.StringVar(value="1.0")
        ttk.Entry(form, textvariable=self.book_duration_var, width=20).grid(row=3, column=1, sticky=tk.W, pady=4)

        ttk.Button(form, text="Check Availability & Book", command=self._do_booking).grid(
            row=4, column=0, columnspan=2, pady=12
        )

        note = ttk.Label(self.book_frame,
                         text="Note: Booking rules (max duration & hours) are enforced automatically based on the selected campus.",
                         font=("Segoe UI", 9), foreground="#333")
        note.pack(anchor=tk.W, pady=8)

    def _populate_resource_combo(self):
        if not self.current_campus_id:
            self.book_resource_combo["values"] = []
            return
        resources = db.get_resources_by_campus(self.current_campus_id, active_only=True)
        self._resource_map = {f"{r['name']} (ID:{r['resource_id']})": r["resource_id"] for r in resources}
        self.book_resource_combo["values"] = list(self._resource_map.keys())
        if self._resource_map:
            self.book_resource_combo.current(0)

    def _do_booking(self):
        if not self.current_campus_id:
            messagebox.showwarning("No Campus", "Please select a campus first.")
            return
        res_key = self.book_resource_var.get()
        if not res_key or res_key not in self._resource_map:
            messagebox.showwarning("Input", "Please select a resource.")
            return
        rid = self._resource_map[res_key]
        date_str = self.book_date_var.get().strip()
        time_str = self.book_time_var.get().strip()
        try:
            duration = float(self.book_duration_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Duration must be a number.")
            return

        ok, msg = db.create_booking(rid, self.user.user_id, self.current_campus_id,
                                    date_str, time_str, duration)
        if ok:
            messagebox.showinfo("Success", msg)
            if hasattr(self, "my_bookings_tree"):
                self._load_my_bookings()
        else:
            messagebox.showerror("Booking Failed", msg)

    # -------------------- Lecturer: My Bookings --------------------
    def _build_my_bookings_tab(self):
        toolbar = ttk.Frame(self.mybook_frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(toolbar, text="Refresh", command=self._load_my_bookings).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Cancel Selected", command=self._cancel_my_booking).pack(side=tk.LEFT, padx=3)

        cols = ("ID", "Resource", "Campus", "Date", "Start", "End", "Duration", "Status")
        self.my_bookings_tree = ttk.Treeview(self.mybook_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.my_bookings_tree.heading(c, text=c)
            self.my_bookings_tree.column(c, width=100)
        self.my_bookings_tree.column("ID", width=50)
        self.my_bookings_tree.pack(fill=tk.BOTH, expand=True)
        self._load_my_bookings()

    def _load_my_bookings(self):
        for i in self.my_bookings_tree.get_children():
            self.my_bookings_tree.delete(i)
        bookings = db.get_user_bookings(self.user.user_id, include_cancelled=True)
        for b in bookings:
            self.my_bookings_tree.insert("", tk.END, values=(
                b["booking_id"], b["resource_name"], b["campus_name"],
                b["booking_date"], b["start_time"], b["end_time"],
                b["duration_hours"], b["status"]
            ))

    def _cancel_my_booking(self):
        sel = self.my_bookings_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a booking to cancel.")
            return
        item = self.my_bookings_tree.item(sel[0])
        bid = item["values"][0]
        if not messagebox.askyesno("Confirm", f"Cancel booking #{bid}?"):
            return
        ok, msg = db.cancel_booking(bid, self.user.user_id, is_admin=False)
        if ok:
            messagebox.showinfo("Success", msg)
            self._load_my_bookings()
        else:
            messagebox.showerror("Failed", msg)

    # -------------------- Admin: Manage Resources --------------------
    def _build_manage_resources_tab(self):
        toolbar = ttk.Frame(self.manage_res_frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(toolbar, text="Add Resource", command=self._add_resource).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Update Selected", command=self._update_resource).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Deactivate Selected", command=self._deactivate_resource).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Refresh", command=self._load_manage_resources).pack(side=tk.LEFT, padx=3)

        cols = ("ID", "Name", "Type", "Capacity", "Description", "Active")
        self.manage_tree = ttk.Treeview(self.manage_res_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.manage_tree.heading(c, text=c)
            self.manage_tree.column(c, width=110)
        self.manage_tree.column("Description", width=200)
        self.manage_tree.pack(fill=tk.BOTH, expand=True)
        self._load_manage_resources()

    def _load_manage_resources(self):
        for i in self.manage_tree.get_children():
            self.manage_tree.delete(i)
        cid = self.current_campus_id or self.user.campus_id
        if not cid:
            return
        resources = db.get_resources_by_campus(cid, active_only=False)
        for r in resources:
            self.manage_tree.insert("", tk.END, values=(
                r["resource_id"], r["name"], r["resource_type"],
                r["capacity"], r.get("description", ""), "Yes" if r["is_active"] else "No"
            ))

    def _add_resource(self):
        cid = self.current_campus_id or self.user.campus_id
        if not cid:
            messagebox.showwarning("Campus", "No campus selected.")
            return
        dialog = ResourceDialog(self.root, "Add Resource")
        if dialog.result:
            name, rtype, capacity, desc = dialog.result
            ok, msg = db.add_resource(cid, name, rtype, capacity, desc)
            if ok:
                messagebox.showinfo("Success", msg)
                self._load_manage_resources()
                self._load_resources()
                if hasattr(self, "book_resource_combo"):
                    self._populate_resource_combo()
            else:
                messagebox.showerror("Failed", msg)

    def _update_resource(self):
        sel = self.manage_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a resource first.")
            return
        vals = self.manage_tree.item(sel[0])["values"]
        rid, name, rtype, cap, desc, active = vals
        dialog = ResourceDialog(self.root, "Update Resource",
                                initial=(name, rtype, cap, desc, active == "Yes"))
        if dialog.result:
            name, rtype, capacity, desc, is_active = dialog.result
            ok, msg = db.update_resource(rid, name, rtype, capacity, desc, 1 if is_active else 0)
            if ok:
                messagebox.showinfo("Success", msg)
                self._load_manage_resources()
                self._load_resources()
            else:
                messagebox.showerror("Failed", msg)

    def _deactivate_resource(self):
        sel = self.manage_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a resource first.")
            return
        rid = self.manage_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", "Deactivate this resource?"):
            ok, msg = db.delete_resource(rid)
            messagebox.showinfo("Result", msg)
            self._load_manage_resources()
            self._load_resources()

    # -------------------- Campus Bookings (Admin/Operator) --------------------
    def _build_campus_bookings_tab(self):
        toolbar = ttk.Frame(self.allbook_frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(toolbar, text="Refresh", command=self._load_bookings).pack(side=tk.LEFT, padx=3)
        if self.user.role == "operator":
            ttk.Button(toolbar, text="Show All Campuses", command=self._load_all_bookings).pack(side=tk.LEFT, padx=3)

        cols = ("ID", "Resource", "User", "Date", "Start", "End", "Duration", "Status")
        self.bookings_tree = ttk.Treeview(self.allbook_frame, columns=cols, show="headings", height=16)
        for c in cols:
            self.bookings_tree.heading(c, text=c)
            self.bookings_tree.column(c, width=100)
        self.bookings_tree.pack(fill=tk.BOTH, expand=True)
        self._load_bookings()

    def _load_bookings(self):
        for i in self.bookings_tree.get_children():
            self.bookings_tree.delete(i)
        cid = self.current_campus_id or self.user.campus_id
        if not cid:
            return
        bookings = db.get_campus_bookings(cid, status="active")
        for b in bookings:
            self.bookings_tree.insert("", tk.END, values=(
                b["booking_id"], b["resource_name"], b["user_name"],
                b["booking_date"], b["start_time"], b["end_time"],
                b["duration_hours"], b["status"]
            ))

    def _load_all_bookings(self):
        for i in self.bookings_tree.get_children():
            self.bookings_tree.delete(i)
        bookings = db.get_all_bookings()
        for b in bookings:
            self.bookings_tree.insert("", tk.END, values=(
                b["booking_id"], f"{b['resource_name']} ({b['campus_name']})",
                b["user_name"], b["booking_date"], b["start_time"],
                b["end_time"], b["duration_hours"], b["status"]
            ))

    # -------------------- Reports --------------------
    def _build_reports_tab(self):
        toolbar = ttk.Frame(self.report_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(toolbar, text="Generate Cross-Campus Report", command=self._show_cross_report).pack(side=tk.LEFT)

        self.report_text = tk.Text(self.report_frame, wrap=tk.WORD, font=("Consolas", 10), height=25)
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self._show_cross_report()

    def _show_cross_report(self):
        self.report_text.delete("1.0", tk.END)
        report = db.get_cross_campus_report()
        self.report_text.insert(tk.END, "=== CROSS-CAMPUS COMPARATIVE REPORT ===\n\n")
        self.report_text.insert(tk.END, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for r in report:
            self.report_text.insert(tk.END, f"Campus: {r['campus_name']}\n")
            self.report_text.insert(tk.END, f"  Policy        : Max {r['max_duration']}h | Hours {r['hours']}\n")
            self.report_text.insert(tk.END, f"  Total Bookings: {r['total_bookings']}\n")
            self.report_text.insert(tk.END, f"  Active        : {r['active_bookings']}\n")
            self.report_text.insert(tk.END, f"  Avg Duration  : {r['average_duration']} hours\n")
            self.report_text.insert(tk.END, "  Top Resources :\n")
            if r["top_resources"]:
                for name, cnt in r["top_resources"]:
                    self.report_text.insert(tk.END, f"    - {name}: {cnt} bookings\n")
            else:
                self.report_text.insert(tk.END, "    (none yet)\n")
            self.report_text.insert(tk.END, "\n" + "-" * 50 + "\n\n")

    def _build_admin_report_tab(self):
        toolbar = ttk.Frame(self.report_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(toolbar, text="Refresh Campus Report", command=self._show_admin_report).pack(side=tk.LEFT)

        self.report_text = tk.Text(self.report_frame, wrap=tk.WORD, font=("Consolas", 10), height=25)
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self._show_admin_report()

    def _show_admin_report(self):
        self.report_text.delete("1.0", tk.END)
        cid = self.current_campus_id or self.user.campus_id
        if not cid:
            self.report_text.insert(tk.END, "No campus selected.")
            return
        c = self.campuses.get(cid, {})
        r = db.get_campus_report(cid)
        self.report_text.insert(tk.END, f"=== CAMPUS REPORT: {c.get('name', '')} ===\n\n")
        self.report_text.insert(tk.END, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        self.report_text.insert(tk.END, f"Total Bookings : {r['total_bookings']}\n")
        self.report_text.insert(tk.END, f"Active Bookings: {r['active_bookings']}\n")
        self.report_text.insert(tk.END, f"Avg Duration   : {r['average_duration']} hours\n\n")
        self.report_text.insert(tk.END, "Most Frequently Used Resources:\n")
        for name, cnt in r["top_resources"]:
            self.report_text.insert(tk.END, f"  - {name}: {cnt}\n")
        if not r["top_resources"]:
            self.report_text.insert(tk.END, "  (no data yet)\n")

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            # Relaunch login
            new_root = tk.Tk()
            app = Application(new_root)
            new_root.mainloop()


class ResourceDialog(simpledialog.Dialog):
    """Dialog for adding/updating a resource."""

    def __init__(self, parent, title, initial=None):
        self.initial = initial  # (name, type, capacity, desc) or with active
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.name_var = tk.StringVar(value=self.initial[0] if self.initial else "")
        ttk.Entry(master, textvariable=self.name_var, width=35).grid(row=0, column=1, pady=3)

        ttk.Label(master, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.type_var = tk.StringVar(value=self.initial[1] if self.initial else "Lab")
        ttk.Combobox(master, textvariable=self.type_var,
                     values=["Lab", "Room", "Hall", "Equipment", "Other"],
                     width=33).grid(row=1, column=1, pady=3)

        ttk.Label(master, text="Capacity:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.cap_var = tk.StringVar(value=str(self.initial[2]) if self.initial else "1")
        ttk.Entry(master, textvariable=self.cap_var, width=35).grid(row=2, column=1, pady=3)

        ttk.Label(master, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.desc_var = tk.StringVar(value=self.initial[3] if self.initial else "")
        ttk.Entry(master, textvariable=self.desc_var, width=35).grid(row=3, column=1, pady=3)

        if self.initial and len(self.initial) > 4:
            self.active_var = tk.BooleanVar(value=self.initial[4])
            ttk.Checkbutton(master, text="Active", variable=self.active_var).grid(
                row=4, column=1, sticky=tk.W, pady=3
            )
        return master

    def apply(self):
        try:
            capacity = int(self.cap_var.get())
        except ValueError:
            capacity = 1
        name = self.name_var.get().strip()
        rtype = self.type_var.get().strip()
        desc = self.desc_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required.", parent=self)
            self.result = None
            return
        if hasattr(self, "active_var"):
            self.result = (name, rtype, capacity, desc, self.active_var.get())
        else:
            self.result = (name, rtype, capacity, desc)


class Application:
    """Application controller: manages login -> main window transition."""

    def __init__(self, root: tk.Tk):
        self.root = root
        db.init_db()  # Ensure DB is ready
        self.login = LoginWindow(root, self._on_login_success)

    def _on_login_success(self, user: User):
        # Clear login widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("980x640")
        MainApplication(self.root, user)


def main():
    root = tk.Tk()
    # Optional: set a modern theme if available
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
