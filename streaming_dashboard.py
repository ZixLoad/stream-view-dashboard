import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import webview
import json
import requests

SAVE_FILE = "streams.json"

LIVE_KEYWORDS = ["LIVE", "EN DIRECT", "방송중", "스트리밍 중"]


class StreamManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuration principale
        self.title("Stream Manager")
        self.geometry("700x700")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Gestion de la fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Charger les images/icônes des boutons
        self.switch_on_image = ctk.CTkImage(Image.open("switch-on.png"), size=(40, 40))
        self.switch_off_image = ctk.CTkImage(Image.open("switch-off.png"), size=(40, 40))
        self.preview_image = ctk.CTkImage(Image.open("preview.png"), size=(40, 40))
        self.add_image = ctk.CTkImage(Image.open("add.png"), size=(40, 40))
        self.update_image = ctk.CTkImage(Image.open("update.png"), size=(40, 40))
        self.delete_image = ctk.CTkImage(Image.open("cross.png"), size=(40, 40))

        # Charger les logos des services
        self.twitch_logo = ctk.CTkImage(Image.open("twitch.png"), size=(30, 30))
        self.bili_logo = ctk.CTkImage(Image.open("bili.png"), size=(30, 30))
        self.soop_logo = ctk.CTkImage(Image.open("soop.png"), size=(30, 30))

        self.default_font = ("Segoe UI", 14)
        self.default_font_bold = ("Segoe UI", 16, "bold")

        # Charger les flux sauvegardés
        self.streams = self.load_streams()

        # Construire l'interface graphique principale
        self.create_main_interface()

    def create_main_interface(self):
        """
        Crée l'interface principale.
        """
        # Frame pour ajouter un flux
        self.add_stream_frame = ctk.CTkFrame(self, corner_radius=15)
        self.add_stream_frame.pack(pady=20, padx=25, fill="x")

        self.stream_name_label = ctk.CTkLabel(
            self.add_stream_frame, text="Name :", font=self.default_font
        )
        self.stream_name_label.grid(row=0, column=0, padx=10, pady=10)

        self.stream_input = ctk.CTkEntry(
            self.add_stream_frame, placeholder_text="Ex: Twitch Channel", font=self.default_font
        )
        self.stream_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.url_label = ctk.CTkLabel(self.add_stream_frame, text="Link :", font=self.default_font)
        self.url_label.grid(row=1, column=0, padx=10, pady=10)

        self.url_input = ctk.CTkEntry(
            self.add_stream_frame, placeholder_text="https://www...", font=self.default_font
        )
        self.url_input.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.add_button = ctk.CTkButton(
            self.add_stream_frame, text="", image=self.add_image, command=self.add_stream, width=40, fg_color="transparent"
        )
        self.add_button.grid(row=0, column=2, pady=10, padx=10)

        self.update_button = ctk.CTkButton(
            self.add_stream_frame, text="", image=self.update_image, command=self.update_all_statuses, width=40,
            fg_color="transparent"
        )
        self.update_button.grid(row=1, column=2, pady=10, padx=10)

        self.add_stream_frame.columnconfigure(1, weight=1)

        # Frame scrollable pour afficher les flux
        self.streams_frame = ctk.CTkScrollableFrame(self, width=660, height=450, corner_radius=15)
        self.streams_frame.pack(pady=10, padx=25, fill="both", expand=True)

        # Rafraîchir les flux affichés
        self.refresh_streams()

    def add_stream(self):
        """
        Ajoute un flux (nom + URL) à la liste des flux.
        """
        name = self.stream_input.get().strip()
        url = self.url_input.get().strip()

        if not name or not url:
            messagebox.showwarning("Warning", "Please enter a name and a valid URL.")
            return

        if name in self.streams:
            messagebox.showerror("Error", f"The stream '{name}' already exists.")
            return

        # Déterminer le logo basé sur l'URL
        logo = self.get_logo_for_url(url)

        # Ajouter le flux dans le dictionnaire de flux
        self.streams[name] = {"url": url, "live": False, "logo": logo}
        self.save_streams()
        self.refresh_streams()

        # Vider les champs d'entrée
        self.stream_input.delete(0, 'end')
        self.url_input.delete(0, 'end')

    def refresh_streams(self):
        """
        Rafraîchit visuellement la liste des flux.
        """
        for widget in self.streams_frame.winfo_children():
            widget.destroy()

        for name, info in self.streams.items():
            # Créer un cadre pour chaque flux
            frame = ctk.CTkFrame(self.streams_frame, corner_radius=20, fg_color="#222222")
            frame.pack(pady=10, padx=10, fill="x", expand=True)

            frame.columnconfigure(1, weight=1)

            # Logo du service
            if info.get("logo"):
                logo_label = ctk.CTkLabel(frame, text="", image=info["logo"])
                logo_label.grid(row=0, column=0, padx=10, pady=10)

            # Label du nom de flux
            title_label = ctk.CTkLabel(frame, text=name, font=self.default_font_bold)
            title_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

            # Bouton ON/OFF
            status_image = self.switch_on_image if info["live"] else self.switch_off_image
            switch_button = ctk.CTkButton(
                frame, image=status_image, text="", width=50, fg_color="#333333", command=lambda: self.toggle_live_status(name)
            )
            switch_button.grid(row=0, column=2, padx=10, pady=10)

            # Bouton Preview
            preview_button = ctk.CTkButton(
                frame, image=self.preview_image, text="", command=lambda url=info["url"]: self.preview_stream(url), width=50,
                fg_color="#333333"
            )
            preview_button.grid(row=0, column=3, padx=10, pady=10)

            # Bouton Croix (supprimer)
            delete_button = ctk.CTkButton(
                frame, image=self.delete_image, text="", command=lambda stream_name=name: self.remove_stream(stream_name),
                width=50, fg_color="#333333"
            )
            delete_button.grid(row=0, column=4, padx=10, pady=10, sticky="e")

    def toggle_live_status(self, name):
        """
        Inverse le statut 'live' du flux (oui/non).
        """
        if name in self.streams:
            self.streams[name]["live"] = not self.streams[name]["live"]
            self.save_streams()
            self.refresh_streams()

    def check_twitch_live_status(self, streamer_name):
        """
        Vérifie si une chaîne Twitch est en ligne.
        """
        url = f"https://www.twitch.tv/{streamer_name}"
        headers = {
            "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and '"isLiveBroadcast":true' in response.text:
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de la vérification Twitch : {e}")
            return False


    def check_soop_live_status(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return False

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text().upper()

            return any(keyword in page_text for keyword in LIVE_KEYWORDS)
        except Exception as e:
            print(f"Erreur SOOP : {e}")
            return False
        
    def update_all_statuses(self):
        """
        Met à jour les statuts live pour tous les flux.
        """
        for name, info in self.streams.items():
            platform = self.get_platform_from_url(info["url"])

            if platform == "twitch":
                streamer_name = info["url"].split("/")[-1]
                self.streams[name]["live"] = self.check_twitch_live_status(streamer_name)
            elif platform == "sooplive":
                self.streams[name]["live"] = self.check_soop_live_status(info["url"])
            else:
                self.streams[name]["live"] = False


        self.save_streams()
        self.refresh_streams()

    def remove_stream(self, name):
            """
            Supprime un flux de la liste.
            """
            if name in self.streams:
                del self.streams[name]
                self.save_streams()
                self.refresh_streams()

    def get_platform_from_url(self, url):
        """
        Détecte la plateforme en fonction de l’URL.
        """
        if "twitch.tv" in url:
            return "twitch"
        elif "bilibili" in url:
            return "bilibili"
        elif "soop" in url:
            return "sooplive"
        else:
            return "unknown"

    def get_logo_for_url(self, url):
        """
        Attribue un logo en fonction de la plateforme.
        """
        platform = self.get_platform_from_url(url)
        if platform == "twitch":
            return self.twitch_logo
        elif platform == "bilibili":
            return self.bili_logo
        elif platform == "sooplive":
            return self.soop_logo
        else:
            return None

    def save_streams(self):
        """
        Sauvegarde les streams dans un fichier JSON.
        """
        try:
            streams_to_save = {
                name: {"url": info["url"], "live": info["live"], "platform": self.get_platform_from_url(info["url"])}
                for name, info in self.streams.items()
            }

            with open(SAVE_FILE, "w") as file:
                json.dump(streams_to_save, file, indent=4)
        except Exception as e:
            print(f"Erreur pendant la sauvegarde : {e}")

    def load_streams(self):
        """
        Charge les flux depuis un fichier JSON pour ajouter les logos appropriés.
        """
        try:
            with open(SAVE_FILE, "r") as file:
                data = json.load(file)
                for name, stream in data.items():
                    platform = stream.get("platform", "unknown")
                    if platform == "twitch":
                        stream["logo"] = self.twitch_logo
                    elif platform == "bilibili":
                        stream["logo"] = self.bili_logo
                    elif platform == "sooplive":
                        stream["logo"] = self.soop_logo
                    else:
                        stream["logo"] = None
                return data
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Erreur : fichier JSON corrompu.")
            return {}

    def preview_stream(self, url):
        """
        Ouvre une prévisualisation du flux dans WebView.
        """
        try:
            webview.create_window("Stream Preview", url)
            webview.start()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir : {e}")

    def on_close(self):
        """
        Sauvegarde les flux avant la fermeture.
        """
        self.save_streams()
        self.destroy()


if __name__ == "__main__":
    app = StreamManagerApp()
    app.mainloop()
