Network Scanner

What This App Does:

Network Scanner is a GUI-based utility designed to map local network environments. While traditional network discovery tools rely on command-line interfaces that can be unintuitive for standard users, this application abstracts that complexity into a single-click interface.

Core functionalities include:

    Auto-detection of the local subnet routing.

    ARP-based network discovery to bypass standard ICMP (ping) firewalls.

    MAC address OUI resolution via public APIs to identify hardware vendors.

    Heuristic device fingerprinting to categorize hardware types (e.g., PC, Mobile, IoT).

    Threaded execution to maintain a responsive UI during blocking network and API calls.

The Goal of This Project:
There are more advanced tools than this but they execute many more features, unlike this application. This application is solely focused on network scanning and made sure that everyone can use and understand it.

How It Works:

This application bridges low-level packet manipulation with a graphical interface, completely packaged as a native Debian application.

Network Discovery & Root Execution:

The core scanner relies on scapy to craft and send raw ARP requests inside Ethernet broadcast frames. Because manipulating raw sockets requires administrative privileges on Linux, the execution flow must be elevated. To prevent the GUI from failing under root execution—a common issue when user environment variables are dropped by security policies—the application utilizes a custom bash wrapper. This wrapper safely passes the $DISPLAY and $XAUTHORITY variables to the elevated pkexec process, ensuring the CustomTkinter interface renders correctly under root.

System Integration & Dock Icon Handling:

Packaging a Python GUI into a native .deb installer presents a specific challenge with Linux desktop window managers. By default, Linux tracks running applications by their process names to assign dock and taskbar icons. When running a PyInstaller-compiled Python binary with elevated privileges, the desktop environment loses the process tree link, typically resulting in a default "gear" fallback icon in the dock.

To solve this and provide a seamless native experience, the application explicitly binds the GUI window to the .desktop shortcut using the X11 window class property:

    Inside the application code, the Tkinter instance uses iconphoto(True, icon) to force the icon globally onto the window manager.

    The hidden window ID broadcasted by the Tkinter framework was identified by querying the X server (xprop WM_CLASS), revealing the broadcast string as Tk.

    The StartupWMClass=Tk directive was mapped directly into the application's .desktop file within the Debian package structure.