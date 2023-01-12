import numpy as np
import pandas as pd
import bs4
from bs4 import BeautifulSoup
import requests
import csv
import datetime
import time
import hashlib
import os  
import matplotlib.pyplot as plt
import seaborn as sns
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options 



sns.set(rc={'figure.facecolor':'white'})
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
now = datetime.datetime.now()

USERNAME = "user's username"
PASSWORD = "user's password"
GAMES_URL = "https://www.chess.com/games/archive?gameOwner=other_game&username=" + USERNAME + "&gameType=live&gameResult=&opponent=&opening=&color=&gameTourTeam=&" + "timeSort=desc&rated=rated&startDate%5Bdate%5D=08%2F01%2F2013&endDate%5Bdate%5D=" + str(now.month) + "%2F" + str(now.day) + "%2F" + str(now.year) + "&ratingFrom=&ratingTo=&page="
LOGIN_URL = "https://www.chess.com/login"

driver = webdriver.Chrome("chromedriver.exe", options=options)
driver.get(LOGIN_URL)
driver.find_element_by_id("username").send_keys(USERNAME)
driver.find_element_by_id("password").send_keys(PASSWORD)
driver.find_element_by_id("login").click()
time.sleep(5)

tables = []
game_links = []

for page_number in range(4):
    driver.get(GAMES_URL + str(page_number + 1))
    time.sleep(5)
    tables.append(
        pd.read_html(
            driver.page_source, 
            attrs={'class':'table-component table-hover archive-games-table'}
        )[0]
    )
    
    table_user_cells = driver.find_elements_by_class_name('archive-games-user-cell')
    for cell in table_user_cells:
        link = cell.find_elements_by_tag_name('a')[0]
        game_links.append(link.get_attribute('href'))
        
driver.close()

games = pd.concat(tables)

identifier = pd.Series(
    games['Players'] + str(games['Result']) + str(games['Moves']) + games['Date']
).apply(lambda x: x.replace(" ", ""))

games.insert(
    0, 
    'GameId', 
    identifier.apply(lambda x: hashlib.sha1(x.encode("utf-8")).hexdigest())
)

print(games())

new = games.Players.str.split(" ", n=5, expand=True)
new = new.drop([1,4], axis=1)
new[2] = new[2].str.replace('(','').str.replace(')','').astype(int)
new[5] = new[5].str.replace('(','').str.replace(')','').astype(int)
games['White Player'] = new[0]
games['White Rating'] = new[2]
games['Black Player'] = new[3]
games['Black Rating'] = new[5]

result = games.Result.str.split(" ", expand=True)
games['White Result'] = result[0]
games['Black Result'] = result[1]


games = games.rename(columns={"Unnamed: 0": "Time"})
games = games.drop(['Players', 'Unnamed: 6', 'Result', 'Accuracy'], axis=1)

conditions = [
        (games['White Player'] == USERNAME) & (games['White Result'] == '1'),
        (games['Black Player'] == USERNAME) & (games['Black Result'] == '1'),
        (games['White Player'] == USERNAME) & (games['White Result'] == '0'),
        (games['Black Player'] == USERNAME) & (games['Black Result'] == '0'),
        ]
choices = ["Win", "Win", "Loss", "Loss"]
games['W/L'] = np.select(conditions, choices, default="Draw")

conditions = [
        (games['White Player'] == USERNAME),
        (games['Black Player'] == USERNAME)
        ]
choices = ["White", "Black"]
games['Colour'] = np.select(conditions, choices)

conditions = [
        (games['White Player'] == USERNAME),
        (games['Black Player'] == USERNAME)
        ]
choices = [games['White Rating'], games['Black Rating']]
games['My Rating'] = np.select(conditions, choices)

conditions = [
        (games['White Player'] != USERNAME),
        (games['Black Player'] != USERNAME)
        ]
choices = [games['White Rating'], games['Black Rating']]
games['Opponent Rating'] = np.select(conditions, choices)

games['Rating Difference'] = games['Opponent Rating'] - games['My Rating']

conditions = [
        (games['White Player'] == USERNAME) & (games['White Result'] == '1'),
        (games['Black Player'] == USERNAME) & (games['Black Result'] == '1')
        ]
choices = [1, 1]
games['Win'] = np.select(conditions, choices)

conditions = [
        (games['White Player'] == USERNAME) & (games['White Result'] == '0'),
        (games['Black Player'] == USERNAME) & (games['Black Result'] == '0')
        ]
choices = [1, 1]
games['Loss'] = np.select(conditions, choices)

conditions = [
        (games['White Player'] == USERNAME) & (games['White Result'] == '½'),
        (games['Black Player'] == USERNAME) & (games['Black Result'] == '½')
        ]
choices = [1, 1]
games['Draw'] = np.select(conditions, choices)

games['Year'] = pd.to_datetime(games['Date']).dt.to_period('Y')

games['Link'] = pd.Series(game_links)
games["Date"] = pd.to_datetime(
    games["Date"].str.replace(",", "") + " 00:00", format = '%b %d %Y %H:%M'
)

print(games())


fig = plt.figure(figsize=(14,8))
plt.title("How does the time affect my games?")
sns.countplot(data=games, x='Time', hue="W/L", palette={"Win":"#CCCCCC", "Loss":"Grey", "Draw":"White"}, edgecolor="Black");

fig, ax = plt.subplots(figsize=(15,6))
ax.set_title("How does my piece colour affect my games?")
sns.barplot(data=games, x='Colour', y='Win', palette={"Black": "Grey", "White": "White"}, edgecolor="black", ax=ax);