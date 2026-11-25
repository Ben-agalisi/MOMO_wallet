"""Tkinter screens and event handlers for the MoMo wallet."""

import tkinter as tk
from tkinter import messagebox, ttk

from analytics import summarize_transactions
from models import InsufficientFundsError
from storage import WalletDataError, WalletStore


class WalletApp(tk.Tk):
    """Class-based login, registration, and wallet interface."""

    def __init__(self):
        super().__init__()
        self.title("MoMo Wallet | Learning Sandbox")
        self.geometry("980x720")
        self.minsize(820, 620)
        self.configure(background="#ffcc00")
        self.store = WalletStore()
        self.current_account = None
        self._configure_style()
        try:
            self.store.load()
        except WalletDataError as error:
            messagebox.showerror("Wallet data error", f"{error}\n\nThe app will close without changing the saved file.", parent=self)
            self.destroy()
            return
        self.show_gate()

    def _configure_style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#ffcc00")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffcc00", foreground="#1d1d1d", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground="#1d1d1d")
        style.configure("Subtitle.TLabel", foreground="#4a3b00")
        style.configure("Card.TLabel", background="#ffffff", foreground="#1d1d1d", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", font=("Segoe UI", 13, "bold"))
        style.configure("Metric.TLabel", background="#ffffff", foreground="#1d1d1d", font=("Segoe UI", 15, "bold"))
        style.configure("Balance.TLabel", background="#ffffff", foreground="#1d1d1d", font=("Segoe UI", 25, "bold"))
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 10), background="#ffcc00", foreground="#1d1d1d")
        style.map("TButton", background=[("active", "#f2b800")])
        style.configure("Accent.TButton", background="#1d1d1d", foreground="#ffcc00")
        style.map("Accent.TButton", background=[("active", "#333333")])
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#ffcc00", foreground="#1d1d1d")
        style.map("Treeview", background=[("selected", "#1d1d1d")], foreground=[("selected", "#ffcc00")])

    def _clear_screen(self):
        for child in self.winfo_children():
            child.destroy()

    def _header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="MoMo Wallet", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="SIMULATED SANDBOX", foreground="#1d1d1d").pack(side="right", padx=8)

    def show_gate(self, register_mode=False):
        """Display login or registration before any wallet data is visible."""
        self.current_account = None
        self._clear_sensitive_inputs()
        self._clear_screen()
        outer = ttk.Frame(self, padding=32)
        outer.pack(fill="both", expand=True)
        self._header(outer)
        ttk.Label(outer, text="Learn mobile money, one transaction at a time.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 18))

        tabs = ttk.Frame(outer)
        tabs.pack(anchor="w", pady=(0, 12))
        ttk.Button(tabs, text="Log in", command=lambda: self.show_gate(False)).pack(side="left", padx=(0, 8))
        ttk.Button(tabs, text="Create account", command=lambda: self.show_gate(True)).pack(side="left")

        card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        card.pack(fill="x", anchor="n")
        if register_mode:
            self._registration_form(card)
        else:
            self._login_form(card)

        note = "Demo login: personal 0240000000 / PIN 1234   ·   merchant 0200000000 / PIN 4321"
        ttk.Label(outer, text=note, style="Subtitle.TLabel", wraplength=850).pack(anchor="w", pady=(16, 0))
        ttk.Label(outer, text="This learning app does not connect to a real payment network.", style="Subtitle.TLabel").pack(anchor="w", pady=(6, 0))

    def _login_form(self, parent):
        ttk.Label(parent, text="Welcome back", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        self.login_phone = tk.StringVar()
        self.login_pin = tk.StringVar()
        ttk.Label(parent, text="Phone number", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        phone_entry = ttk.Entry(parent, textvariable=self.login_phone, width=35)
        phone_entry.grid(row=1, column=1, sticky="ew", padx=(20, 0), pady=6)
        ttk.Label(parent, text="4-digit PIN", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        pin_entry = ttk.Entry(parent, textvariable=self.login_pin, show="•", width=35)
        pin_entry.grid(row=2, column=1, sticky="ew", padx=(20, 0), pady=6)
        parent.columnconfigure(1, weight=1)
        ttk.Button(parent, text="Log in securely", style="Accent.TButton", command=self._login).grid(row=3, column=1, sticky="e", pady=(14, 0))
        pin_entry.bind("<Return>", lambda _event: self._login())
        phone_entry.focus_set()

    def _registration_form(self, parent):
        ttk.Label(parent, text="Create a wallet", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        self.register_name = tk.StringVar()
        self.register_phone = tk.StringVar()
        self.register_pin = tk.StringVar()
        self.register_type = tk.StringVar(value="Personal")
        fields = (
            ("Account holder name", ttk.Entry(parent, textvariable=self.register_name)),
            ("Phone (10–15 digits)", ttk.Entry(parent, textvariable=self.register_phone)),
            ("Create 4-digit PIN", ttk.Entry(parent, textvariable=self.register_pin, show="•")),
        )
        for row, (label, entry) in enumerate(fields, start=1):
            ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=6)
            entry.grid(row=row, column=1, sticky="ew", padx=(20, 0), pady=6)
        ttk.Label(parent, text="Account type", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Combobox(parent, textvariable=self.register_type, values=("Personal", "Merchant"), state="readonly", width=32).grid(row=4, column=1, sticky="ew", padx=(20, 0), pady=6)
        parent.columnconfigure(1, weight=1)
        ttk.Button(parent, text="Create account", style="Accent.TButton", command=self._register_account).grid(row=5, column=1, sticky="e", pady=(14, 0))

    def _login(self):
        account = self.store.authenticate(self.login_phone.get().strip(), self.login_pin.get())
        if account is None:
            messagebox.showerror("Login failed", "Phone number or PIN is incorrect.", parent=self)
            self.login_pin.set("")
            return
        self.login_pin.set("")
        self.current_account = account
        self.show_wallet()

    def _register_account(self):
        account = None
        try:
            account = self.store.register(
                self.register_name.get(), self.register_phone.get(),
                self.register_pin.get(), self.register_type.get(),
            )
            self.store.save()
        except (ValueError, WalletDataError) as error:
            if account in self.store.accounts:
                self.store.accounts.remove(account)
            messagebox.showerror("Could not create account", str(error), parent=self)
            return
        messagebox.showinfo("Account created", "Your wallet is ready. Log in with your phone and PIN.", parent=self)
        self.show_gate()
        self.login_phone.set(account.phone)

    def show_wallet(self):
        """Build the authenticated balance, actions, and transaction history."""
        self._clear_screen()
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text=f"Hello, {self.current_account.name}", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="SIMULATED SANDBOX", foreground="#1d1d1d").pack(side="left", padx=16)
        ttk.Button(header, text="Lock / switch account", command=self._lock).pack(side="right")

        self.wallet_tabs = ttk.Notebook(outer)
        self.wallet_tabs.pack(fill="both", expand=True)
        wallet_tab = ttk.Frame(self.wallet_tabs, padding=(0, 12))
        dashboard_tab = ttk.Frame(self.wallet_tabs, padding=(0, 12))
        self.wallet_tabs.add(wallet_tab, text="Wallet actions")
        self.wallet_tabs.add(dashboard_tab, text="Wallet dashboard")

        summary = ttk.Frame(wallet_tab, style="Card.TFrame", padding=18)
        summary.pack(fill="x", pady=(0, 14))
        summary_header = ttk.Frame(summary, style="Card.TFrame")
        summary_header.pack(fill="x")
        ttk.Label(summary_header, text=f"{self.current_account.account_type} wallet  ·  {self.current_account.phone}", style="CardTitle.TLabel").pack(side="left")
        self.balance_visible = False
        self.balance_toggle_button = ttk.Button(summary_header, text="👁 Show balance", command=self._toggle_balance)
        self.balance_toggle_button.pack(side="right")
        self.balance_label = ttk.Label(summary, text="", style="Balance.TLabel")
        self.balance_label.pack(anchor="w", pady=(8, 0))

        dashboard = ttk.Frame(dashboard_tab, style="Card.TFrame", padding=14)
        dashboard.pack(fill="x", expand=True)
        dashboard_header = ttk.Frame(dashboard, style="Card.TFrame")
        dashboard_header.pack(fill="x", pady=(0, 8))
        ttk.Label(dashboard_header, text="Wallet dashboard", style="CardTitle.TLabel").pack(side="left")
        self.dashboard_period = tk.StringVar(value="Last 30 days")
        period_picker = ttk.Combobox(
            dashboard_header, textvariable=self.dashboard_period,
            values=("Last 7 days", "Last 30 days", "All time"),
            state="readonly", width=16,
        )
        period_picker.pack(side="right")
        period_picker.bind("<<ComboboxSelected>>", self._refresh_dashboard)

        metrics = ttk.Frame(dashboard, style="Card.TFrame")
        metrics.pack(fill="x", pady=(0, 6))
        self.dashboard_values = {}
        for column, (label, key) in enumerate((
            ("Money in", "money_in"),
            ("Money out", "money_out"),
            ("Fees", "fees"),
            ("Transactions", "transaction_count"),
        )):
            metrics.columnconfigure(column, weight=1)
            tile = ttk.Frame(metrics, style="Card.TFrame")
            tile.grid(row=0, column=column, sticky="w", padx=(0, 8))
            ttk.Label(tile, text=label, style="Card.TLabel").pack(anchor="w")
            value = ttk.Label(tile, text="—", style="Metric.TLabel")
            value.pack(anchor="w", pady=(2, 0))
            self.dashboard_values[key] = value

        self.dashboard_chart = tk.Canvas(
            dashboard, height=100, background="#ffffff", highlightthickness=0,
        )
        self.dashboard_chart.pack(fill="x", expand=True)
        self.dashboard_chart.bind("<Configure>", self._draw_dashboard_chart)

        actions = ttk.Frame(wallet_tab, style="Card.TFrame", padding=16)
        actions.pack(fill="x", pady=(0, 14))
        ttk.Label(actions, text="Deposit & cash out", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Label(actions, text="Amount (GH₵)", style="Card.TLabel").grid(row=1, column=0, sticky="w")
        self.amount_value = tk.StringVar()
        amount_entry = ttk.Entry(actions, textvariable=self.amount_value, width=18)
        amount_entry.grid(row=1, column=1, sticky="w", padx=8)
        amount_entry.bind("<Return>", lambda _event: self._perform("deposit"))
        chip_frame = ttk.Frame(actions, style="Card.TFrame")
        chip_frame.grid(row=1, column=2, sticky="w", padx=(4, 12))
        for amount in (10, 50, 100):
            ttk.Button(chip_frame, text=f"GH₵ {amount}", command=lambda value=amount: self.amount_value.set(str(value))).pack(side="left", padx=2)
        ttk.Button(actions, text="Deposit", command=lambda: self._perform("deposit")).grid(row=1, column=3, padx=4)
        ttk.Button(actions, text="Cash out", command=lambda: self._perform("cashout")).grid(row=1, column=4, padx=4)

        ttk.Label(actions, text="Recipient phone number", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.recipient_value = tk.StringVar()
        recipient_entry = ttk.Entry(actions, textvariable=self.recipient_value, width=32)
        recipient_entry.grid(row=2, column=1, columnspan=4, sticky="ew", padx=8, pady=(12, 0))
        ttk.Label(actions, text="Network provider", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.network_provider = tk.StringVar(value="MTN")
        ttk.Combobox(
            actions, textvariable=self.network_provider,
            values=("MTN", "Telecel", "AT"), state="readonly", width=20,
        ).grid(row=3, column=1, sticky="w", padx=8, pady=(8, 0))
        ttk.Label(actions, text="Simulated choice only", style="Card.TLabel").grid(row=3, column=2, sticky="w", padx=4, pady=(8, 0))
        ttk.Button(actions, text="Send money", style="Accent.TButton", command=lambda: self._perform("transfer")).grid(row=3, column=3, columnspan=2, padx=4, pady=(8, 0))
        actions.columnconfigure(5, weight=1)

        self.history_visible = False
        self.history_toggle_button = ttk.Button(
            wallet_tab, text="▼ Show transaction history", command=self._toggle_history,
        )
        self.history_toggle_button.pack(anchor="w", pady=(0, 8))
        self.history_card = ttk.Frame(wallet_tab, style="Card.TFrame", padding=14)
        toolbar = ttk.Frame(self.history_card, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Mini statement", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(toolbar, text="View receipt", command=self._show_receipt).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Export .txt", command=self._export_statement).pack(side="right")
        columns = ("time", "type", "amount", "fee", "reference", "details")
        self.history = ttk.Treeview(self.history_card, columns=columns, show="headings", selectmode="browse")
        headings = {"time": "Date / time", "type": "Transaction", "amount": "Amount", "fee": "Fee", "reference": "Reference", "details": "Details"}
        widths = {"time": 145, "type": 130, "amount": 95, "fee": 80, "reference": 95, "details": 250}
        for column in columns:
            self.history.heading(column, text=headings[column])
            self.history.column(column, width=widths[column], minwidth=70, anchor="w")
        self.history.pack(fill="both", expand=True)
        self.history.bind("<Double-1>", lambda _event: self._show_receipt())
        self._refresh_wallet()

    def _perform(self, action):
        """Validate and run one wallet action, then persist its result."""
        try:
            amount = float(self.amount_value.get().strip())
            if action == "deposit":
                transaction = self.current_account.deposit(amount)
            elif action == "cashout":
                transaction = self.current_account.withdraw(amount)
            else:
                recipient_phone = self.recipient_value.get().strip()
                if not recipient_phone:
                    raise ValueError("Enter the phone number of the person you want to send money to.")
                recipient = self.store.get_account(recipient_phone)
                network_provider = self.network_provider.get()
                if recipient is None:
                    transaction = self.current_account.transfer_to_phone(
                        recipient_phone, amount, network_provider,
                    )
                else:
                    transaction = self.current_account.transfer_to(
                        recipient, amount, network_provider,
                    )
        except (ValueError, InsufficientFundsError) as error:
            messagebox.showerror("Transaction not completed", str(error), parent=self)
            return
        self.amount_value.set("")
        if action == "transfer":
            self.recipient_value.set("")
        self._refresh_wallet()
        try:
            self.store.save()
        except WalletDataError as error:
            messagebox.showerror(
                "Transaction completed, save failed",
                f"The transaction is visible for this session, but could not be saved. "
                f"Please resolve the file issue before closing the app.\n\n{error}",
                parent=self,
            )
            return
        amount_text = f"GH₵ {transaction.amount:.2f}"
        if action == "deposit":
            title = "Deposit successful"
            message = f"You have deposited {amount_text} successfully."
        elif action == "cashout":
            title = "Cash out allowed"
            message = f"Cash out of {amount_text} is allowed and successful in this simulation."
        else:
            title = "Money sent successfully"
            balance_text = (
                f"GH₵ {self.current_account.balance:,.2f}"
                if self.balance_visible else "hidden. Click 'Show balance' to view it"
            )
            recipient_name = (
                f"{recipient.name} ({recipient.phone})"
                if recipient is not None else recipient_phone
            )
            message = (
                f"You have sent {amount_text} to {recipient_name} "
                f"via {network_provider} successfully.\n"
                f"Your new balance is {balance_text}."
            )
            if recipient is None:
                message += (
                    "\nThis is a simulation only; the recipient is not registered "
                    "in this app, so their in-app wallet balance cannot be updated."
                )
        messagebox.showinfo(title, message, parent=self)

    def _refresh_wallet(self):
        self.balance_label.configure(
            text=f"GH₵ {self.current_account.balance:,.2f}" if self.balance_visible else "GH₵ ••••••"
        )
        self.balance_toggle_button.configure(text="🙈 Hide balance" if self.balance_visible else "👁 Show balance")
        for item in self.history.get_children():
            self.history.delete(item)
        for index, transaction in reversed(list(enumerate(self.current_account.transactions))):
            self.history.insert("", "end", iid=str(index), values=(
                transaction.timestamp, transaction.kind, f"GH₵ {transaction.amount:.2f}",
                f"GH₵ {transaction.fee:.2f}", transaction.reference, transaction.details,
            ))
        self._refresh_dashboard()

    def _refresh_dashboard(self, _event=None):
        """Update dashboard totals and chart for the selected time period."""
        period_days = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "All time": None,
        }.get(self.dashboard_period.get())
        totals = summarize_transactions(
            self.current_account.transactions, period_days,
        )
        for key in ("money_in", "money_out", "fees"):
            self.dashboard_values[key].configure(text=f"GH₵ {totals[key]:,.2f}")
        self.dashboard_values["transaction_count"].configure(
            text=str(totals["transaction_count"]),
        )
        self._draw_dashboard_chart()

    def _draw_dashboard_chart(self, _event=None):
        """Draw a compact incoming-versus-outgoing bar chart on the canvas."""
        if not hasattr(self, "dashboard_chart") or self.current_account is None:
            return
        period_days = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "All time": None,
        }.get(self.dashboard_period.get())
        totals = summarize_transactions(
            self.current_account.transactions, period_days,
        )
        canvas = self.dashboard_chart
        canvas.delete("all")
        width = max(canvas.winfo_width(), 360)
        height = max(canvas.winfo_height(), 100)
        baseline = height - 23
        max_bar_height = height - 48
        largest = max(totals["money_in"], totals["money_out"])
        bar_width = min(150, width * 0.22)
        bars = (
            (width * 0.35, totals["money_in"], "Money in", "#ffcc00"),
            (width * 0.70, totals["money_out"], "Money out", "#1d1d1d"),
        )
        for center, amount, label, color in bars:
            bar_height = max_bar_height * amount / largest if largest else 0
            canvas.create_rectangle(
                center - bar_width / 2, baseline - bar_height,
                center + bar_width / 2, baseline,
                fill=color, outline="",
            )
            canvas.create_text(
                center, baseline - bar_height - 9,
                text=f"GH₵ {amount:,.2f}", fill="#1d1d1d",
                font=("Segoe UI", 9, "bold"),
            )
            canvas.create_text(
                center, baseline + 12, text=label, fill="#4a3b00",
                font=("Segoe UI", 9),
            )

    def _toggle_balance(self):
        """Reveal or mask the account balance on request."""
        self.balance_visible = not self.balance_visible
        self._refresh_wallet()

    def _toggle_history(self):
        """Show or hide the transaction history on request."""
        self.history_visible = not self.history_visible
        if self.history_visible:
            self.history_card.pack(fill="both", expand=True)
            self.history_toggle_button.configure(text="▲ Hide transaction history")
        else:
            self.history_card.pack_forget()
            self.history_toggle_button.configure(text="▼ Show transaction history")

    def _show_receipt(self):
        selection = self.history.selection()
        if not selection:
            messagebox.showinfo("Select a transaction", "Choose a transaction row to view its receipt.", parent=self)
            return
        transaction = self.current_account.transactions[int(selection[0])]
        messagebox.showinfo("Transaction receipt", f"MOMO WALLET — RECEIPT\nSimulated Sandbox\n\n{transaction}", parent=self)

    def _export_statement(self):
        try:
            filename = self.store.export_statement(self.current_account)
        except WalletDataError as error:
            messagebox.showerror("Export failed", str(error), parent=self)
            return
        messagebox.showinfo("Statement exported", f"Saved readable transaction history to:\n{filename}", parent=self)

    def _lock(self):
        """Clear the active account and sensitive form values before logout."""
        self.current_account = None
        self.show_gate()

    def _clear_sensitive_inputs(self):
        """Forget PINs, transfer contacts, and amounts when leaving a screen."""
        for name in ("login_pin", "register_pin", "amount_value", "recipient_value"):
            variable = getattr(self, name, None)
            if variable is not None:
                variable.set("")