#!/usr/bin/env python3
# run.py für Home Assistant Add-on

import os
import json
import requests
from bs4 import BeautifulSoup
import asyncio
import time
from telegram import Bot

class HomeAssistantWebScraper:
    def __init__(self):
        # Konfiguration aus Home Assistant Add-on laden
        self.config = self.load_config()
        self.bot = Bot(token=self.config['telegram_token'])
        self.session = requests.Session()
        
    def load_config(self):
        """Lädt Konfiguration aus Home Assistant"""
        try:
            with open('/data/options.json', 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            # Fallback auf Umgebungsvariablen
            return {
                'telegram_token': os.getenv('TELEGRAM_TOKEN', ''),
                'chat_id': os.getenv('CHAT_ID', ''),
                'login_url': os.getenv('LOGIN_URL', ''),
                'search_url': os.getenv('SEARCH_URL', ''),
                'username': os.getenv('USERNAME', ''),
                'password': os.getenv('PASSWORD', ''),
                'username_field': os.getenv('USERNAME_FIELD', 'username'),
                'password_field': os.getenv('PASSWORD_FIELD', 'password'),
                'interval_minutes': int(os.getenv('INTERVAL_MINUTES', '2'))
            }
    
    def log(self, message):
        """Logging für Home Assistant"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def login_to_website(self):
        """Loggt sich auf der Webseite ein"""
        try:
            self.log("Starte Login-Prozess...")
            response = self.session.get(self.config['login_url'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            login_form = soup.find('form')
            if login_form:
                action = login_form.get('action', self.config['login_url'])
                if not action.startswith('http'):
                    if action.startswith('/'):
                        base_url = '/'.join(self.config['login_url'].split('/')[:3])
                        action = base_url + action
                    else:
                        action = self.config['login_url'] + '/' + action
            else:
                action = self.config['login_url']
            
            login_data = {
                self.config['username_field']: self.config['username'],
                self.config['password_field']: self.config['password']
            }
            
            if login_form:
                hidden_inputs = login_form.find_all('input', {'type': 'hidden'})
                for hidden_input in hidden_inputs:
                    name = hidden_input.get('name')
                    value = hidden_input.get('value')
                    if name and value:
                        login_data[name] = value
            
            login_response = self.session.post(action, data=login_data)
            
            if login_response.status_code == 200:
                self.log("Login erfolgreich!")
                return True
            else:
                self.log(f"Login fehlgeschlagen. Status Code: {login_response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Fehler beim Login: {e}")
            return False
    
    def search_for_phrase(self, phrase="Achteraus (€)"):
        """Durchsucht die Webseite nach der Phrase"""
        try:
            response = self.session.get(self.config['search_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            lines = page_text.split('\n')
            found_lines = []
            
            for line in lines:
                if phrase in line:
                    clean_line = line.strip()
                    if clean_line:
                        found_lines.append(clean_line)
            
            return found_lines
            
        except Exception as e:
            self.log(f"Fehler beim Durchsuchen der Seite: {e}")
            return []
    
    async def send_telegram_message(self, message):
        """Sendet Nachricht über Telegram"""
        try:
            await self.bot.send_message(chat_id=self.config['chat_id'], text=message)
            self.log("Telegram-Nachricht gesendet!")
        except Exception as e:
            self.log(f"Fehler beim Senden der Telegram-Nachricht: {e}")
    
    def format_results(self, found_lines):
        """Formatiert die Ergebnisse für Telegram"""
        if not found_lines:
            return "🔍 Keine neuen 'Achteraus (€)' Einträge gefunden."
        
        message = f"🔍 Neue 'Achteraus (€)' Einträge gefunden ({len(found_lines)}):\n\n"
        
        for i, line in enumerate(found_lines, 1):
            message += f"{i}. {line}\n"
        
        if len(message) > 4000:
            message = message[:4000] + "...\n\n⚠️ Nachricht gekürzt"
        
        return message
    
    async def run_single_check(self):
        """Führt eine einzelne Überprüfung durch"""
        self.log("Starte Überprüfung...")
        
        # Login
        if not self.login_to_website():
            await self.send_telegram_message("❌ Login fehlgeschlagen!")
            return
        
        # Suche nach Phrase
        found_lines = self.search_for_phrase()
        
        # Nur senden wenn etwas gefunden wurde
        if found_lines:
            message = self.format_results(found_lines)
            await self.send_telegram_message(message)
            self.log(f"Gefunden: {len(found_lines)} Einträge")
        else:
            self.log("Keine neuen Einträge gefunden")
    
    async def run_continuous(self):
        """Läuft kontinuierlich mit dem konfigurierten Intervall"""
        self.log(f"Starte kontinuierliche Überwachung (alle {self.config['interval_minutes']} Minuten)")
        
        while True:
            try:
                await self.run_single_check()
                await asyncio.sleep(self.config['interval_minutes'] * 60)
            except KeyboardInterrupt:
                self.log("Script gestoppt")
                break
            except Exception as e:
                self.log(f"Unerwarteter Fehler: {e}")
                await asyncio.sleep(60)  # 1 Minute warten bei Fehlern

async def main():
    scraper = HomeAssistantWebScraper()
    await scraper.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())
