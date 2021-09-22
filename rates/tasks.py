import requests
from bs4 import BeautifulSoup
from .models import Rate
from datetime import datetime

page = requests.get("https://www.ibjarates.com/")
soup = BeautifulSoup(page.content,'html.parser')
rate24k = soup.find_all(id='lblrate24K')[0].get_text()

rate = Rate(on = datetime.today(),price = rate24k,
        source='ijlbarates.com',source_name='ijlbarates')
rate.save()
