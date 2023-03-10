import sys

from bs4 import BeautifulSoup
import requests

url = "https://docs.google.com/spreadsheets/d/1OEWNWCZgWcWbpeGSmqm_uktQsuMI7Y2Aveo6mzmk80I/edit#gid=20773121"
r = requests.get(url)
soup = BeautifulSoup(r.content, "lxml")
table = soup.find("tbody")
print(table.find("tr").find("td").text)