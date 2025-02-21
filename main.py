import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import configparser
from colorama import Fore, Style
from pynput import keyboard
import re
import threading
import requests
import winsound
import discord


sniper_active = True

class MewtStyle():
    MAIN = "\x1b[38;2;247;184;207m"

# Глобальная переменная для конфигурации
config = configparser.ConfigParser()

# Загрузка данных из удаленного файла
def read_file():
    try:
        response = requests.get('https://raw.githubusercontent.com/Bac0nio/Keywords/refs/heads/main/keywords.json')
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.RequestException as e:
        print(f'Failed to read file: {e}')
        return None

# Загрузка данных
data = read_file()
if data:
    disallowed = data.get('disallowed', [])
    allowedG = data.get('allowedG', [])
    allowedJ = data.get('allowedJ', [])
    allowedV = data.get('allowedV', [])
    allowedD = data.get('allowedD', [])
    Gdisallowed = data.get('Gdisallowed', [])
    Jdisallowed = data.get('Jdisallowed', [])
    Vdisallowed = data.get('Vdisallowed', [])
    Ddisallowed = data.get('Ddisallowed', [])
    blocked_users_ids = data.get('blocked_users_ids', [])
else:
    print('No data was retrieved.')
    disallowed = []
    allowedG = []
    allowedJ = []
    allowedV = []
    allowedD = []
    Gdisallowed = []
    Jdisallowed = []
    Vdisallowed = []
    Ddisallowed = []
    blocked_users_ids = []

# Инициализация бота
bot = discord.Client()  # Используем discord.Client() для selfbot

# Функции для проверки ключевых слов

def checkForGlitch(content):
    if any(word.lower() in content.lower() for word in disallowed):
        return False
    if any(word.lower() in content.lower() for word in Gdisallowed):
        return False
    if any(word.lower() in content.lower() for word in allowedG):
        return True
    return False

def checkForDream(content):
    if any(word.lower() in content.lower() for word in disallowed):
        return False
    if any(word.lower() in content.lower() for word in Ddisallowed):
        return False
    if any(word.lower() in content.lower() for word in allowedD):
        return True
    return False

def checkForJester(content):
    if any(word.lower() in content.lower() for word in disallowed):
        return False
    if any(word.lower() in content.lower() for word in Jdisallowed):
        return False
    if any(word.lower() in content.lower() for word in allowedJ):
        return True
    return False

def checkForCoin(content):
    if any(word.lower() in content.lower() for word in disallowed):
        return False
    if any(word.lower() in content.lower() for word in Vdisallowed):
        return False
    if any(word.lower() in content.lower() for word in allowedV):
        return True
    return False

# Функция для конвертации ссылок
def convert_roblox_link(url):
    game_pattern = r'https:\/\/www\.roblox\.com\/games\/(\d+)\/[^?]+\?privateServerLinkCode=(\d+)'
    share_pattern = r'https:\/\/www\.roblox\.com\/share\?code=([a-f0-9]+)&type=([A-Za-z]+)'

    match_game = re.match(game_pattern, url)
    if match_game:
        place_id = match_game.group(1)
        link_code = match_game.group(2)
        if place_id != '15532962292':
            return None
        return f'roblox://placeID={place_id}&linkCode={link_code}'

    match_share = re.match(share_pattern, url)
    if match_share:
        code = match_share.group(1)
        share_type = match_share.group(2)
        return f'roblox://navigation/share_links?code={code}&type={share_type}'

    return None

# Функция для открытия ссылок
def open_link_in_thread(input_string):
    url_pattern = re.compile(r'https?://[^\s]+')
    match = url_pattern.search(input_string)
    if match:
        link = convert_roblox_link(match.group(0))
        if link:
            os.startfile(link)  # Открываем ссылку
        else:
            print('No valid Roblox deep link found or The provided link is not for Sols RNG.')
    else:
        print('No valid URL found in the input string.')

def check_mentions(content):
    mention_pattern = r'@(everyone|here|&[0-9]+)'
    return bool(re.search(mention_pattern, content))

# Функция для загрузки пользовательских серверов
def load_custom_servers():
    try:
        with open('servers.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Обработчик событий для discord.py-self
@bot.event
async def on_ready():
    os.system('cls')
    print(Style.BRIGHT + f"> Current User: {MewtStyle.MAIN}{Style.BRIGHT}{bot.user.name}{Fore.WHITE}{Style.BRIGHT} ")
    print(Fore.RESET + Style.RESET_ALL)

# Функция для одновременного выполнения действий
def handle_detection_parallel(detection_type, message_content, server_name):
    # Открываем ссылку в отдельном потоке
    threading.Thread(target=open_link_in_thread, args=(message_content,)).start()
    
    # Выводим сообщение
    print(Style.BRIGHT + f"> {detection_type} detected: {MewtStyle.MAIN}{Style.BRIGHT}{server_name}{Fore.WHITE}{Style.BRIGHT}")
    print(Style.BRIGHT + f"> Message content: {MewtStyle.MAIN}{Style.BRIGHT}{message_content}{Fore.WHITE}{Style.BRIGHT}")
    print(Fore.RESET + Style.RESET_ALL)
    
    # Воспроизводим звук
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

@bot.event
async def on_message(message):
    global sniper_active
    if not sniper_active:
        return

    custom_servers = load_custom_servers()

    server_id = message.guild.id if message.guild else None
    channel_id = message.channel.id

    # Указанные каналы, которые нужно проверять всегда
    specified_channels = ['1282542323590496277', '1282543762425516083']

    is_custom_server = False
    use_keywords = True
    only_ping = False
    triggers = []
    for server in custom_servers:
        if str(server['server_id']) == str(server_id) and str(channel_id) in server['channel_ids']:
            is_custom_server = True
            use_keywords = server.get('useKeywords', True)
            only_ping = server.get('onlyPing', False)
            triggers = server.get('triggers', [])
            break

    # Проверка на указанные каналы
    is_specified_channel = str(channel_id) in specified_channels

    if (is_custom_server or is_specified_channel) and 'roblox.com' in message.content.lower():
        is_blocked = message.author.id in blocked_users_ids

        server_name = message.guild.name if message.guild else "DM"

        if only_ping and not check_mentions(message.content):
            return

        if is_blocked:
            print(f"{Fore.RED}{Style.BRIGHT}> THIS IS FROM A BLOCKED USER: {message.content}{Style.RESET_ALL}")
            return

        if any(trigger.lower() in message.content.lower() for trigger in triggers):
            handle_detection_parallel("Trigger", message.content, server_name)

        # Проверка ключевых слов (работает только если useKeywords = True)
        if use_keywords or is_specified_channel:
            if config.getboolean('sniping', 'glitchsniping') and checkForGlitch(message.content):
                handle_detection_parallel("Glitch", message.content, server_name)

            if config.getboolean('sniping', 'dreamsniping') and checkForDream(message.content):
                handle_detection_parallel("Dream", message.content, server_name)

            if config.getboolean('sniping', 'jestersniping') and checkForJester(message.content):
                handle_detection_parallel("Jester", message.content, server_name)

            if config.getboolean('sniping', 'voidCoinsniping') and checkForCoin(message.content):
                handle_detection_parallel("Void Coin", message.content, server_name)

def random_public_server():
    print("test")

def stop_spamming_and_teleport():
    print("test1")

def stop_sniper_for_2_minutes():
    global sniper_active
    sniper_active = False
    print(f"{Fore.RED}{Style.BRIGHT}> Sniper stopped for 2 minutes{Style.RESET_ALL}")
    time.sleep(120)
    sniper_active = True
    print(f"{Fore.GREEN}{Style.BRIGHT}> Sniper resumed{Style.RESET_ALL}")

def on_press(key):
    try:
        random_server_key = config.get('Hotkeys', 'open_roblox', fallback='-').lower()
        stop_spam_key = config.get('Hotkeys', 'stop_teleport', fallback='-').lower()
        stop_sniper_key = config.get('Hotkeys', 'stop_sniper', fallback='-').lower()
        
        random_server_enabled = config.getboolean('Hotkeys', 'open_roblox_toggle', fallback=False)
        stop_spam_enabled = config.getboolean('Hotkeys', 'stop_teleport_toggle', fallback=False)
        stop_sniper_enabled = config.getboolean('Hotkeys', 'stop_sniper_toggle', fallback=False)
        
        pressed_key = key.char.lower() if hasattr(key, 'char') else None
        
        if pressed_key == stop_sniper_key and sniper_active and stop_sniper_enabled:
            threading.Thread(target=stop_sniper_for_2_minutes).start()
        
        if pressed_key == random_server_key and random_server_enabled:
            random_public_server()
        
        if pressed_key == stop_spam_key and stop_spam_enabled:
            stop_spamming_and_teleport()
    except AttributeError:
        pass

keyboard_listener = keyboard.Listener(on_press=on_press)
keyboard_listener.start()

# Класс CustomServer
class CustomServer:
    def __init__(self, data=None):
        self.serverName = data.get('server_name', 'Unnamed Server') if data else 'Unnamed Server'
        self.serverID = data.get('server_id', '') if data else ''
        self.channelIDs = data.get('channel_ids', []) if data else []
        self.triggers = data.get('triggers', []) if data else []
        self.useBotKeywords = data.get('useKeywords', False) if data else False
        self.onlyPing = data.get('onlyPing', False) if data else False  # Новое поле

    def to_dict(self):
        return {
            'server_name': self.serverName,
            'server_id': self.serverID,
            'channel_ids': self.channelIDs,
            'triggers': self.triggers,
            'useKeywords': self.useBotKeywords,
            'onlyPing': self.onlyPing  # Новое поле
        }

# Класс CustomServersGUI
class CustomServersGUI:
    def __init__(self, master):
        self.master = master
        self.custom_servers = self.load_custom_servers()
        self.editing_index = None
        self.create_custom_servers_tab()

    def load_custom_servers(self):
        try:
            with open('servers.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_custom_servers(self):
        with open('servers.json', 'w') as file:
            json.dump(self.custom_servers, file, indent=4)

    def create_custom_servers_tab(self):
        self.servers_listbox = tk.Listbox(self.master, height=10, width=50)
        self.servers_listbox.pack(padx=10, pady=10)

        for server in self.custom_servers:
            self.servers_listbox.insert(tk.END, server.get('server_name', 'Unnamed Server'))

        self.edit_button = tk.Button(self.master, text="Edit Selected Server", command=self.edit_custom_server)
        self.edit_button.pack(padx=10, pady=5)

        self.add_button = tk.Button(self.master, text="Add New Server", command=self.open_custom_servers_window)
        self.add_button.pack(padx=10, pady=5)

        self.delete_button = tk.Button(self.master, text="Delete Selected Server", command=self.delete_custom_server)
        self.delete_button.pack(padx=10, pady=5)

    def refresh_servers_listbox(self):
        self.servers_listbox.delete(0, tk.END)
        for server in self.custom_servers:
            self.servers_listbox.insert(tk.END, server.get('server_name', 'Unnamed Server'))

    def open_custom_servers_window(self, server_data=None):
        if server_data is None:
            server_data = {}

        self.popup_window = tk.Toplevel(self.master)
        self.popup_window.title("Custom Servers Configuration")
        self.popup_window.geometry("500x500")
        self.popup_window.resizable(0, 0)

        self.server_name_label = tk.Label(self.popup_window, text="Server Name:")
        self.server_name_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')

        self.server_name_entry = tk.Entry(self.popup_window, width=30)
        self.server_name_entry.grid(row=0, column=1, padx=10, pady=5)

        if server_data:
            self.server_name_entry.insert(0, server_data.get('server_name', ''))

        self.server_id_label = tk.Label(self.popup_window, text="Server ID:")
        self.server_id_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')

        self.server_id_entry = tk.Entry(self.popup_window, width=30)
        self.server_id_entry.grid(row=1, column=1, padx=10, pady=5)

        if server_data:
            self.server_id_entry.insert(0, server_data.get('server_id', ''))

        self.channel_ids_label = tk.Label(self.popup_window, text="Channel IDs:")
        self.channel_ids_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')

        self.channel_ids_listbox = tk.Listbox(self.popup_window, height=4, width=20, selectmode=tk.EXTENDED)
        self.channel_ids_listbox.grid(row=2, column=1, padx=10, pady=5, sticky='w')

        if server_data:
            for channel_id in server_data.get('channel_ids', []):
                self.channel_ids_listbox.insert(tk.END, channel_id)

        self.use_keywords_var = tk.BooleanVar(value=server_data.get('useKeywords', True))
        self.use_keywords_check = tk.Checkbutton(self.popup_window, text="Use Keywords?", variable=self.use_keywords_var)
        self.use_keywords_check.grid(row=2, column=2, padx=10, pady=5)

        self.only_ping_var = tk.BooleanVar(value=server_data.get('onlyPing', False))
        self.only_ping_check = tk.Checkbutton(self.popup_window, text="Only Ping?", variable=self.only_ping_var)
        self.only_ping_check.grid(row=6, column=2, padx=10, pady=5)

        self.channel_id_entry = tk.Entry(self.popup_window, width=20)
        self.channel_id_entry.grid(row=4, column=1, padx=10, pady=5, sticky='w')

        self.add_channel_button = tk.Button(self.popup_window, text="Add Channel ID", command=self.add_channel_id)
        self.add_channel_button.grid(row=4, column=2, padx=10, pady=5)

        self.remove_channel_button = tk.Button(self.popup_window, text="Remove Selected", command=self.remove_channel_id)
        self.remove_channel_button.grid(row=5, column=1, padx=10, pady=5, sticky='w')

        self.triggers_label = tk.Label(self.popup_window, text="Triggers:")
        self.triggers_label.grid(row=6, column=0, padx=10, pady=5, sticky='w')

        self.triggers_listbox = tk.Listbox(self.popup_window, height=6, width=30, selectmode=tk.EXTENDED)
        self.triggers_listbox.grid(row=6, column=1, padx=10, pady=5, sticky='w')

        if server_data:
            for trigger in server_data.get('triggers', []):
                self.triggers_listbox.insert(tk.END, trigger)

        self.triggers_entry = tk.Entry(self.popup_window, width=20)
        self.triggers_entry.grid(row=7, column=1, padx=10, pady=5, sticky='w')

        self.add_trigger_button = tk.Button(self.popup_window, text="Add Trigger", command=self.add_trigger)
        self.add_trigger_button.grid(row=7, column=2, padx=10, pady=5)

        self.remove_trigger_button = tk.Button(self.popup_window, text="Remove Selected", command=self.remove_trigger)
        self.remove_trigger_button.grid(row=8, column=1, padx=10, pady=5, sticky='w')

        self.save_button = tk.Button(self.popup_window, text="Save All", command=self.save_all_data)
        self.save_button.grid(row=9, column=1, padx=10, pady=10)

    def save_all_data(self):
        server_name = self.server_name_entry.get().strip()
        server_id = self.server_id_entry.get().strip()
        channel_ids = [self.channel_ids_listbox.get(i) for i in range(self.channel_ids_listbox.size())]
        triggers = [self.triggers_listbox.get(i) for i in range(self.triggers_listbox.size())]
        use_keywords = self.use_keywords_var.get()
        only_ping = self.only_ping_var.get()

        new_data = {
            'server_name': server_name,
            'server_id': server_id,
            'channel_ids': channel_ids,
            'triggers': triggers,
            'useKeywords': use_keywords,
            'onlyPing': only_ping
        }

        if self.editing_index is not None:
            self.custom_servers[self.editing_index] = new_data
        else:
            self.custom_servers.append(new_data)

        self.save_custom_servers()
        self.refresh_servers_listbox()
        self.popup_window.destroy()

    def add_trigger(self):
        trigger = self.triggers_entry.get().strip()
        if trigger:
            self.triggers_listbox.insert(tk.END, trigger)
            self.triggers_entry.delete(0, tk.END)

    def remove_trigger(self):
        selected_items = self.triggers_listbox.curselection()
        for index in reversed(selected_items):
            self.triggers_listbox.delete(index)

    def add_channel_id(self):
        entry = self.channel_id_entry.get().strip()
        if entry:
            self.channel_ids_listbox.insert(tk.END, entry)
            self.channel_id_entry.delete(0, tk.END)

    def remove_channel_id(self):
        selected_items = self.channel_ids_listbox.curselection()
        for index in reversed(selected_items):
            self.channel_ids_listbox.delete(index)

    def edit_custom_server(self):
        selected_index = self.servers_listbox.curselection()
        if selected_index:
            self.editing_index = selected_index[0]
            server_data = self.custom_servers[self.editing_index]
            self.open_custom_servers_window(server_data)

    def delete_custom_server(self):
        selected_index = self.servers_listbox.curselection()
        if selected_index:
            del self.custom_servers[selected_index[0]]
            self.save_custom_servers()
            self.refresh_servers_listbox()

# Класс SniperGUI
class SniperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sniper Macro v1.6.1")
        self.root.geometry("400x425")
        self.root.resizable(0, 0)

        self.logo = tk.PhotoImage(file="snipercat.png")
        self.root.wm_iconphoto(False, self.logo)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        self.sniping_frame = tk.Frame(self.notebook)
        self.hotkeys_frame = tk.Frame(self.notebook)
        self.custom_servers_frame = tk.Frame(self.notebook)
        self.credits_frame = tk.Frame(self.notebook)

        self.notebook.add(self.sniping_frame, text="Sniping")
        self.notebook.add(self.hotkeys_frame, text="Hotkeys")
        self.notebook.add(self.custom_servers_frame, text="Custom servers")
        self.notebook.add(self.credits_frame, text="Credits")

        self.load_settings()

        self.create_sniping_tab()
        self.create_hotkeys_tab()
        self.create_custom_servers_tab()
        self.create_credits_tab()

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.save_button = tk.Button(button_frame, text="Save Changes and Start Sniping", command=self.save_and_start_sniping)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.discord_button = tk.Button(button_frame, text="Our Discord", image=self.logo, compound=tk.LEFT, command=self.open_discord)
        self.discord_button.pack(side=tk.LEFT, padx=5)

        self.custom_servers = self.load_custom_servers()

    def load_settings(self):
        global config
        config.read('sniper_config.ini')

    def save_settings(self):
        config['sniping'] = {
            'glitchsniping': str(self.glitch_var.get()),
            'dreamsniping': str(self.dream_var.get()),
            'jestersniping': str(self.jester_var.get()),
            'voidCoinsniping': str(self.coin_var.get()),
            'toast_notifications': str(self.toast_var.get()),
            'teleportdelay': str(self.slider_value.get()),
            'token': self.token_entry.get().strip()
        }


        config['Hotkeys'] = {
            'open_roblox': self.random_server_var.get(),
            'open_roblox_toggle': str(self.random_server_check_var.get()),
            'stop_teleport': self.stop_spam_var.get(),
            'stop_teleport_toggle': str(self.stop_spam_check_var.get()),
            'stop_sniper': self.stop_sniper_var.get(),
            'stop_sniper_toggle': str(self.stop_sniper_check_var.get())
        }

        with open('sniper_config.ini', 'w') as configfile:
            config.write(configfile)

    def save_and_start_sniping(self):
        self.save_settings()  # Сохраняем настройки
        token = config.get('sniping', 'token', fallback='')  # Получаем токен из конфигурационного файла
        if token:
            threading.Thread(target=bot.run, args=(token,), daemon=True).start()
            self.root.withdraw()  # Скрываем HUD
        else:
            messagebox.showwarning("Warning", "Token not found in sniper_config.ini")

    def create_sniping_tab(self):
        self.glitch_var = tk.BooleanVar(value=config.getboolean('sniping', 'glitchsniping', fallback=False))
        self.glitch_check = tk.Checkbutton(self.sniping_frame, text="Glitch sniping", variable=self.glitch_var)
        self.glitch_check.grid(row=0, column=0, sticky='w', padx=5, pady=2)

        self.dream_var = tk.BooleanVar(value=config.getboolean('sniping', 'dreamsniping', fallback=False))
        self.dream_check = tk.Checkbutton(self.sniping_frame, text="Dream sniping", variable=self.dream_var)
        self.dream_check.grid(row=1, column=0, sticky='w', padx=5, pady=2)

        self.jester_var = tk.BooleanVar(value=config.getboolean('sniping', 'jestersniping', fallback=False))
        self.jester_check = tk.Checkbutton(self.sniping_frame, text="Jester sniping", variable=self.jester_var)
        self.jester_check.grid(row=2, column=0, sticky='w', padx=5, pady=2)

        self.coin_var = tk.BooleanVar(value=config.getboolean('sniping', 'voidCoinsniping', fallback=False))
        self.coin_check = tk.Checkbutton(self.sniping_frame, text="Void Coin sniping", variable=self.coin_var)
        self.coin_check.grid(row=3, column=0, sticky='w', padx=5, pady=2)

        self.toast_var = tk.BooleanVar(value=config.getboolean('sniping', 'toast_notifications', fallback=True))
        self.toast_check = tk.Checkbutton(self.sniping_frame, text="Sniper Notifications", variable=self.toast_var)
        self.toast_check.grid(row=4, column=0, sticky='w', padx=5, pady=2)

        self.delay_label = tk.Label(self.sniping_frame, text="Set the delay for the merchant teleporter.\n(Increase the delay ONLY if it doesn't write 'ch' correctly.)", anchor='w', justify='left')
        self.delay_label.grid(row=5, column=0, sticky='w', padx=5, pady=5)

        self.slider_value = tk.DoubleVar(value=float(config.get('sniping', 'teleportdelay', fallback=0.3)))
        self.slider = tk.Scale(self.sniping_frame, from_=0, to=1, orient='horizontal', resolution=0.05, variable=self.slider_value)
        self.slider.grid(row=6, column=0, sticky='w', padx=5, pady=2)

        self.token_label = tk.Label(self.sniping_frame, text="Enter a discord token to an account with\naccess to the private server channels.", anchor='w', justify='left')
        self.token_label.grid(row=7, column=0, sticky='w', padx=5, pady=5)

        self.token_entry = tk.Entry(self.sniping_frame, width=40)
        self.token_entry.insert(0, config.get('sniping', 'token', fallback=''))
        self.token_entry.grid(row=8, column=0, sticky='w', padx=5, pady=2)

        self.save_token_btn = tk.Button(self.sniping_frame, text="Save Token", command=self.save_token)
        self.save_token_btn.grid(row=9, column=0, sticky='w', padx=5, pady=10)

    def create_hotkeys_tab(self):
        # Надпись "Set Hotkeys" посередине сверху
        self.set_hotkeys_label = tk.Label(self.hotkeys_frame, text="Set Hotkeys", font=('Arial', 12, 'bold'))
        self.set_hotkeys_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Первый блок: Sends you to a random public server
        self.random_server_label = tk.Label(self.hotkeys_frame, text="Sends you to a random public server", anchor='w', justify='left')
        self.random_server_label.grid(row=1, column=0, sticky='w', padx=0, pady=2)

        self.random_server_var = tk.StringVar(value=config.get('Hotkeys', 'open_roblox', fallback='-'))
        self.random_server_dropdown = ttk.Combobox(
            self.hotkeys_frame, 
            textvariable=self.random_server_var, 
            values=["A", "B", "D", "F", "G", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "-", "=", "[", "]", ";", "'", "/"], 
            state='normal', 
            width=5
        )
        self.random_server_dropdown.grid(row=1, column=1, sticky='w', padx=0, pady=2)

        self.random_server_check_var = tk.BooleanVar(value=config.getboolean('Hotkeys', 'open_roblox_toggle', fallback=False))
        self.random_server_check = tk.Checkbutton(self.hotkeys_frame, variable=self.random_server_check_var)
        self.random_server_check.grid(row=1, column=2, sticky='w', padx=0, pady=2)

        # Второй блок: Stop spamming and teleport to merchant
        self.stop_spam_label = tk.Label(self.hotkeys_frame, text="Stop spamming and teleport to merchant", anchor='w', justify='left')
        self.stop_spam_label.grid(row=2, column=0, sticky='w', padx=0, pady=2)

        self.stop_spam_var = tk.StringVar(value=config.get('Hotkeys', 'stop_teleport', fallback='-'))
        self.stop_spam_dropdown = ttk.Combobox(
            self.hotkeys_frame, 
            textvariable=self.stop_spam_var, 
            values=["A", "B", "D", "F", "G", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "-", "=", "[", "]", ";", "'", "/"], 
            state='normal', 
            width=5
        )
        self.stop_spam_dropdown.grid(row=2, column=1, sticky='w', padx=0, pady=2)

        self.stop_spam_check_var = tk.BooleanVar(value=config.getboolean('Hotkeys', 'stop_teleport_toggle', fallback=False))
        self.stop_spam_check = tk.Checkbutton(self.hotkeys_frame, variable=self.stop_spam_check_var)
        self.stop_spam_check.grid(row=2, column=2, sticky='w', padx=0, pady=2)

        # Третий блок: Stop the sniper for 2 minutes
        self.stop_sniper_label = tk.Label(self.hotkeys_frame, text="Stop the sniper for 2 minutes", anchor='w', justify='left')
        self.stop_sniper_label.grid(row=3, column=0, sticky='w', padx=0, pady=2)

        self.stop_sniper_var = tk.StringVar(value=config.get('Hotkeys', 'stop_sniper', fallback='-'))
        self.stop_sniper_dropdown = ttk.Combobox(
            self.hotkeys_frame, 
            textvariable=self.stop_sniper_var, 
            values=["A", "B", "D", "F", "G", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "-", "=", "[", "]", ";", "'", "/"], 
            state='normal', 
            width=5
        )
        self.stop_sniper_dropdown.grid(row=3, column=1, sticky='w', padx=0, pady=2)

        self.stop_sniper_check_var = tk.BooleanVar(value=config.getboolean('Hotkeys', 'stop_sniper_toggle', fallback=False))
        self.stop_sniper_check = tk.Checkbutton(self.hotkeys_frame, variable=self.stop_sniper_check_var)
        self.stop_sniper_check.grid(row=3, column=2, sticky='w', padx=0, pady=2)

    def update_hotkey(self, hotkey_name, new_hotkey):
        config['Hotkeys'][hotkey_name] = new_hotkey
        with open('sniper_config.ini', 'w') as configfile:
            config.write(configfile)

    def open_coordinate_picker(self):
        pass

    def save_token(self):
        token = self.token_entry.get().strip()
        if token:
            config['sniping']['token'] = token
            with open('sniper_config.ini', 'w') as configfile:
                config.write(configfile)
            messagebox.showinfo("Success", "Token saved successfully!")
        else:
            messagebox.showwarning("Warning", "Token cannot be empty!")

    def create_custom_servers_tab(self):
        self.custom_servers_gui = CustomServersGUI(self.custom_servers_frame)

    def create_credits_tab(self):
        pass

    def save_and_close(self):
        self.save_settings()
        self.root.quit()

    def load_custom_servers(self):
        try:
            with open('servers.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def open_discord(self):
        pass

if __name__ == "__main__":
    app = SniperGUI()
    app.root.mainloop()
