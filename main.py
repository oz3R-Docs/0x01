from flask import Flask, render_template
import cloudscraper
from bs4 import BeautifulSoup
import time
import json
import requests
import re
import threading

app = Flask(__name__)

levelIcons = [
    (10, "Level 10", "static/pics/10.png", 2001, float('inf')),
    (9, "Level 9", "static/pics/9.png", 1751, 2000),
    (8, "Level 8", "static/pics/8.png", 1531, 1750),
    (7, "Level 7", "static/pics/7.png", 1351, 1530),
    (6, "Level 6", "static/pics/6.png", 1201, 1350),
    (5, "Level 5", "static/pics/5.png", 1051, 1200),
    (4, "Level 4", "static/pics/4.png", 901, 1050),
    (3, "Level 3", "static/pics/3.png", 751, 900),
    (2, "Level 2", "static/pics/2.png", 501, 750),
    (1, "Level 1", "static/pics/1.png", 100, 500)
]

def fetchPlayerData():
    playerUrl = "https://faceittracker.net/players/oz3R-/refresh"
    matchesUrl = "https://faceittracker.net/players/api/oz3R-?ms=month"
    scraper = cloudscraper.create_scraper()

    while True:
        response = scraper.get(playerUrl)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            playerCard = soup.find(class_="player-card")
            if playerCard:
                playerElo = int(playerCard.find(class_="player-elo").get_text(strip=True).split()[0])
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
                }
                avgResponse = requests.get(matchesUrl, headers=headers)
                if avgResponse.status_code == 200:
                    try:
                        avgData = avgResponse.json()
                        winCount = avgData.get('avgs', {}).get('win', 0)
                        loseCount = avgData.get('avgs', {}).get('lose', 0)
                        matches = avgData.get('mathches', [])
                        eloChange = "N/A"
                        lastMatchInfo = None

                        for match in matches:
                            if match['elo'] == str(playerElo):
                                eloChange = match['EloChange']
                                lastMatchInfo = match
                                break

                        if eloChange != "N/A":
                            eloChange = re.sub(r'[\(\)]', '', eloChange)
                            lastMatchOutput = f"LAST MATCH: {eloChange}PTS"
                            try:
                                eloChangeValue = int(eloChange)
                                lastMatchIcon = "static/pics/greenArrow.png" if eloChangeValue > 0 else "static/pics/redArrow.png"
                            except ValueError:
                                eloChangeValue = 0
                                lastMatchIcon = "static/pics/redArrow.png"
                        else:
                            lastMatchOutput = "LAST MATCH: N/A"
                            lastMatchIcon = ""

                        totalMatches = winCount + loseCount
                        winPercentage = (winCount / totalMatches * 100) if totalMatches > 0 else 0
                        levelIcon = "static/pics/default.png"
                        for level, levelName, iconFile, lowerBound, upperBound in levelIcons:
                            if lowerBound <= playerElo <= upperBound:
                                levelIcon = iconFile
                                break

                        playerData = {
                            'playerElo': playerElo,
                            'win': winCount,
                            'lose': loseCount,
                            'winPercentage': round(winPercentage),
                            'lastMatch': lastMatchOutput,
                            'pics': {
                                'lastMatchIcon': lastMatchIcon,
                                'levelIcon': levelIcon
                            }
                        }

                        with open("static/data.json", "w") as jsonFile:
                            json.dump(playerData, jsonFile, indent=4)

                    except json.JSONDecodeError:
                        print("JSON yanıtı geçersiz. Yanıt içeriği:", avgResponse.text)
                else:
                    print("Ortalama maç verileri alınamadı. Hata kodu:", avgResponse.status_code)
            else:
                print("Index bulunamadı.")
        else:
            print("API yüklenemedi. Hata kodu:", response.status_code)

        time.sleep(15)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    dataThread = threading.Thread(target=fetchPlayerData)
    dataThread.daemon = True
    dataThread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)