import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from urllib.request import urlopen
import json
import censusgeocode as cg
import requests
import urllib
import us
import numpy as np

def f(n):
    return "{:,}".format(n)


URL = 'https://www.pewresearch.org/fact-tank/2018/03/29/h-1b-visa-approvals-by-us-metro-area/#table'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
results = soup.find("table")

h1b_dict = {}
city_metro_dict = {}

for row in results.findAll("tr"):
    cells = row.findAll("td")
    if len(cells) == 0:
        continue
    all_data = cells[0].text
    list_data = all_data.split(",")
    city = list_data[0]
    state = list_data[1]
    city_list = city.split("-")
    state_list = state.split("-")
    h1b_dict[city_list[0].split("–")[0] + "," + state_list[0]] = int(cells[1].text.replace(',', ''))
    city_metro_dict[city_list[0].split("–")[0] + "," + state_list[0]] = all_data

estimated_workers = 200000
total = 0
for item in h1b_dict.items():
    total += item[1]

coeff = estimated_workers / total
foreign_comp = .049
lost_revenue = 87532

fip_list = []
geolocator = Nominatim(user_agent="notte")
for item in h1b_dict.items():
    loc_list = item[0].split(",")
    peeps = item[1] * coeff
    if loc_list[0] == 'Austin':
        fip_list.append((48453, city_metro_dict[item[0]], np.log(item[1]) - 6, f(int(peeps)), f(int(peeps * foreign_comp)), '$' + str(f(int(peeps * lost_revenue)))))
        continue
    if loc_list[0] == 'Houston':
        fip_list.append((48201, city_metro_dict[item[0]],  np.log(item[1]) - 6, f(int(peeps)), f(int(peeps * foreign_comp)), '$' + str(f(int(peeps * lost_revenue)))))
        continue

    state = us.states.lookup(loc_list[1].lstrip())
    try:
        location = geolocator.geocode(loc_list[0] + ", " + str(state) + ", USA")
        params = urllib.parse.urlencode({'latitude': location.latitude, 'longitude':location.longitude, 'format':'json'})
        url = 'https://geo.fcc.gov/api/census/block/find?' + params
        response = requests.get(url)
        data = response.json()
        fip_list.append((data['County']['FIPS'], city_metro_dict[item[0]], np.log(item[1]) - 6, f(int(peeps)), f(int(peeps * foreign_comp)), '$' + str(f(int(peeps * lost_revenue)))))
    except:
        continue

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

df = pd.DataFrame(fip_list,columns = ['fips','Metro Area','scale', 'Lost Workers', 'Lost Buisnesses/Entrepreneurs', 'Lost Worker Revenue']) 

fig = px.choropleth_mapbox(df, geojson=counties, locations='fips', color= 'scale',
                           color_continuous_scale="thermal",
                           range_color=(0, 7),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           hover_data = {'fips':False, 'Metro Area':True, 'Lost Workers':True,'scale':False, 'Lost Buisnesses/Entrepreneurs':True, 'Lost Worker Revenue':True}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()