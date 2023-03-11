import requests
from bs4 import BeautifulSoup

url = "http://www.kjpl.in"
page = requests.get(url)
soup = BeautifulSoup(page.content, "html.parser")
results = soup.find_all("span", class_="gold-rate")
print(results)
