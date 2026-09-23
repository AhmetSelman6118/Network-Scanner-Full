import os
import sys
import time
import socket
import threading
import urllib.request
import customtkinter as ctk
from tkinter import ttk, PhotoImage
import scapy.all as scapy

if os.geteuid() != 0:
    print("Error: Network scanning requires root privileges.")
    print("Please run the app using: sudo venv/bin/python scanner.py")
    sys.exit(1)

def show_splash_screen():
    splash = ctk.CTk()
    splash.overrideredirect(True)
    splash.geometry("600x300")
    splash.configure(fg_color="black")

    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width / 2) - (600 / 2)
    y = (screen_height / 2) - (300 / 2)
    splash.geometry(f'+{int(x)}+{int(y)}')

    label = ctk.CTkLabel(
        splash, 
        text="Created by Ahmet Selman Severge", 
        text_color="#00FF00",
        font=("Courier New", 26, "bold")
    )
    label.place(relx=0.5, rely=0.5, anchor="center")

    splash.after(3000, splash.destroy)
    splash.mainloop()

class NetworkScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Network Scanner")
        
        # Safe icon loading that will never crash the app
        icon_candidates = [
            "/usr/share/icons/hicolor/256x256/apps/network-scanner.png",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png"),
            "icon.png"
        ]
        for path in icon_candidates:
            if os.path.exists(path):
                try:
                    icon = PhotoImage(file=path)
                    self.iconphoto(True, icon)
                    break
                except Exception:
                    pass

        self.geometry("1100x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=20, padx=20, fill="x")

        self.title_label = ctk.CTkLabel(self.top_frame, text="Network Scanner", font=("Arial", 24, "bold"))
        self.title_label.pack(side="left", padx=10)

        self.ip_entry = ctk.CTkEntry(self.top_frame, placeholder_text="e.g. 192.168.1.0/24", width=200)
        self.ip_entry.pack(side="left", padx=20)
        self.ip_entry.insert(0, self.get_local_subnet())

        self.scan_btn = ctk.CTkButton(self.top_frame, text="Scan Network", command=self.start_scan_thread)
        self.scan_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(self.top_frame, text="", text_color="gray")
        self.status_label.pack(side="right", padx=10)

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.setup_table()

    def get_local_subnet(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            parts = ip.split('.')
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except Exception:
            return "192.168.1.0/24"

    def setup_table(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", foreground="white", rowheight=30, 
                        fieldbackground="#2b2b2b", borderwidth=0, font=("Arial", 11))
        style.map('Treeview', background=[('selected', '#2FA572')])
        style.configure("Treeview.Heading", 
                        background="#3d3d3d", foreground="white", 
                        relief="flat", font=("Arial", 12, "bold"))
        style.map("Treeview.Heading", background=[('active', '#4d4d4d')])

        columns = ("IP Address", "MAC Address", "Length", "Hostname", "Brand", "Device Type", "Count")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            
        self.tree.column("IP Address", anchor="center", width=120)
        self.tree.column("MAC Address", anchor="center", width=150)
        self.tree.column("Length", anchor="center", width=80)
        self.tree.column("Hostname", anchor="center", width=180)
        self.tree.column("Brand", anchor="center", width=150)
        self.tree.column("Device Type", anchor="center", width=120)
        self.tree.column("Count", anchor="center", width=60)
        
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

    def get_mac_details(self, mac_address):
        brand = "Unknown"
        device_type = "Unknown"
        
        try:
            url = f"https://api.macvendors.com/{mac_address}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                brand = response.read().decode('utf-8')
        except Exception:
            pass 

        brand_lower = brand.lower()
        if any(keyword in brand_lower for keyword in ["xiaomi", "samsung", "huawei", "oppo", "vivo", "oneplus", "motorola", "nokia", "sony ericsson"]):
            device_type = "Mobile"
        elif any(keyword in brand_lower for keyword in ["intel", "dell", "hp ", "hewlett", "lenovo", "asus", "acer", "msi", "gigabyte", "microsoft"]):
            device_type = "PC / Laptop"
        elif "apple" in brand_lower:
            device_type = "Mobile / Mac"
        elif any(keyword in brand_lower for keyword in ["espressif", "raspberry", "amazon", "google", "nest", "tplink", "netgear", "cisco", "ubiquiti", "broadcom"]):
            device_type = "IoT / Network"
        elif brand != "Unknown":
            device_type = "Other"

        return brand, device_type

    def start_scan_thread(self):
        ip_range = self.ip_entry.get()
        if not ip_range:
            self.status_label.configure(text="Please enter an IP range!", text_color="red")
            return

        self.status_label.configure(text="Scanning & Fetching Brands... Please wait.", text_color="#00FF00")
        self.scan_btn.configure(state="disabled")
        
        for item in self.tree.get_children():
            self.tree.delete(item)

        threading.Thread(target=self.perform_scan, args=(ip_range,), daemon=True).start()

    def perform_scan(self, ip_range):
        try:
            arp_request = scapy.ARP(pdst=ip_range)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast/arp_request
            
            answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]

            results = []
            for sent, received in answered_list:
                try:
                    hostname = socket.gethostbyaddr(received.psrc)[0]
                except socket.herror:
                    hostname = "Unknown"

                brand, device_type = self.get_mac_details(received.hwsrc)
                time.sleep(1) 

                results.append({
                    "ip": received.psrc,
                    "mac": received.hwsrc,
                    "length": f"{len(received)} bytes",
                    "hostname": hostname,
                    "brand": brand,
                    "device_type": device_type,
                    "count": 1
                })

            self.after(0, self.update_table, results)
            
        except Exception as e:
            self.after(0, self.status_label.configure, {"text": f"Error: {str(e)}", "text_color": "red"})
            self.after(0, self.scan_btn.configure, {"state": "normal"})

    def update_table(self, results):
        for client in results:
            self.tree.insert("", "end", values=(
                client["ip"], 
                client["mac"], 
                client["length"], 
                client["hostname"], 
                client["brand"],
                client["device_type"],
                client["count"]
            ))
        
        self.status_label.configure(text=f"Scan complete. Found {len(results)} devices.", text_color="white")
        self.scan_btn.configure(state="normal")

if __name__ == "__main__":
    show_splash_screen()
    app = NetworkScannerApp()
    app.mainloop()