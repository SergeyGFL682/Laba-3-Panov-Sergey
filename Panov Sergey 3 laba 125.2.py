import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone, timedelta
import threading
import time
import json
import os

class Tariff:
    def __init__(self, name, price, data_limit):
        self.name = name
        self.price = price
        self.data_limit = data_limit

    def __str__(self):
        return f"{self.name} — {self.price} грн / {self.data_limit} ГБ"

class Contract:
    def __init__(self, subscriber, tariff, start_date):
        self.subscriber = subscriber
        self.tariff = tariff
        self.start_date = start_date

    def to_dict(self):
        return {
            "subscriber": self.subscriber.name,
            "tariff": self.tariff.name,
            "price": self.tariff.price,
            "data_limit": self.tariff.data_limit,
            "start_date": self.start_date
        }

class Subscriber:
    def __init__(self, name):
        self.name = name
        self.contract = None

class Operator:
    def __init__(self, name):
        self.name = name
        self.tariffs = []
        self.subscribers = []
        self.lock = threading.Lock()

    def add_tariff(self, tariff):
        self.tariffs.append(tariff)

    def sign_contract(self, subscriber, tariff):
        with self.lock:
            time.sleep(2)
            ukraine_tz = timezone(timedelta(hours=3))
            start_date = datetime.now(ukraine_tz).strftime("%Y-%m-%d %H:%M:%S")
            contract = Contract(subscriber, tariff, start_date)
            subscriber.contract = contract
            self.subscribers.append(subscriber)
            self.save_contract(contract)
            return contract

    def save_contract(self, contract):
        data = contract.to_dict()
        file_path = "contracts.json"
        contracts = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    contracts = json.load(f)
                except json.JSONDecodeError:
                    contracts = []
        contracts.append(data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(contracts, f, ensure_ascii=False, indent=4)

    def load_contracts(self):
        file_path = "contracts.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

class App(tk.Tk):
    def __init__(self, operator):
        super().__init__()
        self.title("Мобільний з'язок")
        self.geometry("500x500")
        self.operator = operator
        self.create_main_menu()

    def create_main_menu(self):
        for widget in self.winfo_children():
            widget.destroy()

        ttk.Label(self, text="Оберіть режим", font=("Arial", 16)).pack(pady=20)
        ttk.Button(self, text="Абонент", command=self.subscriber_ui).pack(pady=10)
        ttk.Button(self, text="Оператор", command=self.operator_ui).pack(pady=10)

    def operator_ui(self):
        self.clear()
        tab_control = ttk.Notebook(self)
        tab_add = ttk.Frame(tab_control)
        tab_view = ttk.Frame(tab_control)
        tab_control.add(tab_add, text="Додати тариф")
        tab_control.add(tab_view, text="Угоди абонентів")
        tab_control.pack(expand=1, fill="both")

        name = ttk.Entry(tab_add)
        name.pack(pady=5)
        price = ttk.Entry(tab_add)
        price.pack(pady=5)
        data = ttk.Entry(tab_add)
        data.pack(pady=5)

        for entry, placeholder in zip([name, price, data], ["Назва тарифу", "Ціна", "Інтернет (ГБ)"]):
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e, ent=entry, ph=placeholder: ent.delete(0, tk.END) if ent.get() == ph else None)

        def add():
            try:
                t = Tariff(name.get(), int(price.get()), int(data.get()))
                self.operator.add_tariff(t)
                messagebox.showinfo("Успіх", f"Додано тариф: {t}")
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

        ttk.Button(tab_add, text="Додати тариф", command=add).pack(pady=5)
        ttk.Button(tab_add, text="Назад", command=self.create_main_menu).pack(pady=10)

        contracts = self.operator.load_contracts()
        tree = ttk.Treeview(tab_view, columns=("subscriber", "tariff", "price", "data_limit", "start_date"), show="headings")
        tree.heading("subscriber", text="Ім'я")
        tree.heading("tariff", text="Тариф")
        tree.heading("price", text="Ціна")
        tree.heading("data_limit", text="Інтернет")
        tree.heading("start_date", text="Дата")
        for c in contracts:
            tree.insert("", "end", values=(c["subscriber"], c["tariff"], c["price"], c["data_limit"], c["start_date"]))
        tree.pack(fill="both", expand=True)

    def subscriber_ui(self):
        self.clear()
        ttk.Label(self, text="Абонент", font=("Arial", 14)).pack(pady=10)

        name_entry = ttk.Entry(self)
        name_entry.pack(pady=5)
        name_entry.insert(0, "Ваше ім'я")
        name_entry.bind("<FocusIn>", lambda e: name_entry.delete(0, tk.END) if name_entry.get() == "Ваше ім'я" else None)

        if not self.operator.tariffs:
            ttk.Label(self, text="Тарифів немає").pack()
            return

        selected_tariff = tk.StringVar()
        selected_tariff.set(str(self.operator.tariffs[0]))
        ttk.Label(self, text="Оберіть тариф").pack()
        ttk.OptionMenu(self, selected_tariff, *[str(t) for t in self.operator.tariffs]).pack(pady=5)

        def submit():
            name = name_entry.get()
            tariff_str = selected_tariff.get()
            tariff = next((t for t in self.operator.tariffs if str(t) == tariff_str), None)

            if name and tariff:
                subscriber = Subscriber(name)
                thread = threading.Thread(target=self.sign_thread, args=(subscriber, tariff))
                thread.start()

        ttk.Button(self, text="Оформити угоду", command=submit).pack(pady=10)
        ttk.Button(self, text="Назад", command=self.create_main_menu).pack(pady=10)

    def sign_thread(self, subscriber, tariff):
        contract = self.operator.sign_contract(subscriber, tariff)
        message = f"{subscriber.name} уклав угоду на тариф '{tariff.name}' з {contract.start_date}"
        messagebox.showinfo("Успіх", message)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    op = Operator("Мобільний оператор")
    op.add_tariff(Tariff("Базовий", 100, 10))
    op.add_tariff(Tariff("Стандарт", 150, 20))
    op.add_tariff(Tariff("Преміум", 200, 50))

    app = App(op)
    app.mainloop()
