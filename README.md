# Raspberry Pi Automotive Setup (Audi RNS-E Integration)

Zentrales Konfigurations- und Quellcode-Repository für das Raspberry Pi Infotainment- und CAN-Bus-System.

---

## Modulübersicht & Funktionsbeschreibungen

### 1. `can/` – CAN-Bus Core & Daemons
* **`rns-e_can/can_handler.py`**: Zentraler Dispatcher für eingehende und ausgehende CAN-Frames.
* **`rns-e_can/can_base_function.py`**: Liest Basissignale wie Zündungsstatus (Klemme 15), Beleuchtung und Geschwindigkeitspulse aus.
* **`rns-e_can/can_keyboard_control.py`**: Übersetzt Dreh-/Drückrad- und Tasteneingaben des RNS-E in native Tastaturevents für Linux/Kodi.
* **`audi-rns-overlay/can_daemon.py`**: Hintergrunddienst zur Statusüberwachung (z. B. Rückwärtsgang-Trigger für Rückfahrkamera und Overlays).
* **`audi-rns-overlay/Api_pb2.py`**: Protobuf-Schnittstellendefinition für die Daemon-Kommunikation.

---

### 2. `dis_client/` – Kombiinstrument / FIS Anbindung
* **`ddp_protocol.py`**: Low-Level-Implementierung des Bosch/Audi Display Data Protocol (DDP).
* **`dis_display.py` & `dis_service.py`**: Hauptlogik zur Formatierung und Übertragung der oberen Textzeilen im Tacho-Display.
* **`dis_client/apps/`**: Submodule für verschiedene FIS-Seiten (`nav.py`, `media.py`, `radio.py`, `car_info.py`, `phone.py`, `menu.py`, `settings.py`).

---

### 3. `hudiy/` – Headunit & Video Interface
* **`dark_mode_api.py` & `hudiy_data.py`**: Schnittstelle zur automatischen Tag/Nacht-Umschaltung über das Fahrzeuglicht und Weitergabe von Fahrzeugdaten an HUDIY.
* **`hudiy_run.sh` / `hudiy_startup.sh`**: Startskripte mit Umgebungsvariablen für Wayland/X11-Ausgabe.

---

### 4. `scripts/` – Steuerung & Testwerkzeuge
* **`read_from_canbus.py`**: Logging- und Diagnosewerkzeug zum Auslesen und Parsen von CAN-Frames auf `can0`.
* **`rnse_ops_switcher.py`**: Steuerung der Videoquellenumschaltung für optische Einparkhilfe (OPS) und Rückfahrkamera.
* **`pi_control.py`**: Systemsteuerung für den Pi (kontrollierter Shutdown / Reboot).
* **`testbench.py`**: CAN-Frame-Simulator für Tests am Schreibtisch ohne echtes Fahrzeugnetz.

---

### 5. `system/`, `systemd/` & `vga-edid/` – Hardware & Autostart
* **`vga-edid/install_edid.sh`**: Installiert und erzwingt RNS-E-kompatible Video-Timings über den VGA-Sync-Combiner.
* **`system/config.txt`**: Boot-Konfiguration (MCP2515 Device-Tree-Overlays, Taktfrequenzen, DPI/KMS-Parameter).
* **`system/udev/99-hudiy.rules`**: USB-Zugriffsregeln für Headunit-Konnektivität.
* **`system/network/80-can.network`**: Systemd-Networkd-Definition für das `can0`-Interface.
* **`systemd/*.service`**: Autostart-Units für alle Daemons, Overlay-Dienste und CPU-Performance-Profile.

---

### 6. `kodi/` – Mediacenter Konfiguration
* **`*.xml`**: Benutzereinstellungen (`advancedsettings.xml`, `guisettings.xml`, `favourites.xml`).
* **`keymaps/`**: Tastenbelegungen für die OEM-Steuerung.
* **`playlists/`**: Angepasste Wiedergabelisten und Stream-Scanner.
