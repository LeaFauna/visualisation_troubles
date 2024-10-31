import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# functions
def process_url(url):
    result = requests.get(url)
    content = result.text
    soup = BeautifulSoup(content, 'html.parser')    
    information = []
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns)>= 2:
                ## from here not tested bc error: max retries exceeded with url
                img_tag = columns[0].find('img')
                if img_tag:
                    photo = img_tag['src']
                else:
                    photo = None
                ## to here
                info = columns[1].get_text(strip = True)
                information.append({'Photo': photo, 'Information':info}) # possibly remove photo-part
    return pd.DataFrame(information)

# extract information
def extract_info(text):
    matches = list(re.finditer(r'\)', text))
    if len(matches) <2:
        return "" # if less than 2 ), return empty string
    pos = matches[2].end()
    return text[pos:]

# remove duplicates
def remove_duplicates(df, duplicate_a, duplicate_b):
    if duplicate_a in df.columns and duplicate_b in df.columns:
        result_df = df.drop_duplicates(subset = [duplicate_a, duplicate_b]) # remove duplicates in name & date
        return result_df
    else:
        print("Some columns don't exist in dataframe")
        return df

def add_coords(victims, towns_coords):
    result_df = victims.copy()
    for i, victim_row in victims.iterrows():
        town = victim_row['town']
        town_row = towns_coords[towns_coords['town'] == town]
        if not town_row.empty:
            coordinates = town_row.iloc[0]['coordinates']
            result_df.at[victim_row.name, 'coordinates'] = coordinates
    return result_df

# save to csv
def to_csv(df,filename):
    path = r"C:/Users/lea/DigitalHumanities/msc/SpatialHum/project"
    full_path = f"{path}//{filename}"
    df.to_csv(full_path, index = False)

# Dataset McKeown as basis
df_mckeown = pd.read_excel('C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/McKeown.xlsx')

# Dataset Sutton 
# get html
url_cain = "https://cain.ulster.ac.uk/sutton/chron/index.html"
result_years = requests.get(url_cain)
content_years = result_years.text
soup_years = BeautifulSoup(content_years, 'html.parser')
pretty_soup = soup_years.prettify

all_dfs = []
for a_tag in soup_years.findAll('a',href =True):
    href = a_tag['href']
    if 'chron' in href:
        full_link = requests.compat.urljoin(url_cain,href) # type: ignore
        df_years = pd.DataFrame([[full_link]])
        all_dfs.append(df_years)

df_sutton_chron = pd.concat(all_dfs, ignore_index=True)

df_sutton_chron = df_sutton_chron.rename(columns={0:'links'})
df_sutton_chron = df_sutton_chron[:-1] # deleting last row because links to main page again

# extract information and store content of all years in info_df
df_temp = []
list_of_dfs = []
for url in df_sutton_chron['links']:
    df_temp = process_url(url)
    list_of_dfs.append(df_temp)
    info_df = pd.concat(list_of_dfs,ignore_index=True)
print(info_df)

# change date format
info_df['Information'] = info_df['Information'].str.replace(' January ', '/01/') \
    .str.replace(' February ', '/02/') \
    .str.replace(' March ', '/03/') \
    .str.replace(' April ', '/04/') \
    .str.replace(' May ', '/05/') \
    .str.replace(' June ', '/06/') \
    .str.replace(' July ', '/07/') \
    .str.replace(' August ', '/08/') \
    .str.replace(' September ', '/09/') \
    .str.replace(' October ', '/10/') \
    .str.replace(' November ', '/11/') \
    .str.replace(' December ', '/12/')

# create columns for each variable
# regex date, name, age, location
date = []
name = []
age = []

date_pattern = r'(?<!\d)\d{1,2}/\d{1,2}/\d{4}(?!\d)'
name_pattern = r'\d{4}\s*(.*?)\s*\('
age_pattern = r'\((\d{1,2})\)'

for index, row in info_df.iterrows():
    text=row['Information']
    date_match = re.search(date_pattern,text)# to string?
    name_match = re.search(name_pattern, text)
    age_match = re.search(age_pattern, text)
    if date_match:
        date.append(date_match.group(0))# to string?
    else:
        date.append(None)
    if name_match:
        name.append(name_match.group(1))
    else: name.append(None)
    if age_match:
        age.append(age_match.group(1))
    else:
        age.append(None)

# append all this information into new df_sutton
df_sutton = pd.DataFrame()
df_sutton['Date'] = date
df_sutton['Name'] = name
df_sutton['Age'] = age

# add description of indicent
df_sutton['Description'] = info_df['Information'].apply(extract_info)

to_csv(df_sutton, 'sutton.csv')

df_sutton = pd.read_csv('C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/sutton.csv')

# combine Sutton and McKeown datasets
df_victims = pd.DataFrame()
df_victims = pd.merge(df_mckeown,df_sutton, how="left", on=["Name"])
# remove duplicates
df_victims = remove_duplicates(df_victims, 'Name', 'Date')

to_csv(df_victims, 'victims_notowns.csv')

## manually added towns and saved as victims_towns.csv

df_victims = pd.read_csv('C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/victims_towns.csv')
# add town coordinates
df_towns_coords = pd.read_csv('C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/towns.csv')

merged_df = pd.DataFrame()
merged_df = add_coords(df_victims, df_towns_coords)

merged_df[['gps_x', 'gps_y']] = merged_df['coordinates'].str.split(',', expand = True)

merged_df['age'] = merged_df[['age']].astype('Int64')

to_csv(merged_df, 'victims.csv')