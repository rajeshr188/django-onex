import BeautifulSoup
import requests

from product.models import Rate, RateSource

url = "https://www.kjpl.in/rates"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table", {"class": "table table-striped"})
rows = table.find_all("tr")
for row in rows:
    cols = row.find_all("td")
    cols = [ele.text.strip() for ele in cols]
    if len(cols) > 0:
        rate = Rate()
        rate.metal = Rate.GOLD
        rate.currency = Rate.INR
        rate.purity = cols[0]
        rate.buying_rate = cols[1]
        rate.selling_rate = cols[2]
        rate.rate_source = RateSource.objects.get(name="kjpl")
        rate.save()
rate = Rate.objects.latest("timestamp")
print(rate)
