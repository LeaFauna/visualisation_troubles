from bs4 import BeautifulSoup
import pandas as pd
import os
import chardet # automatically detects character encoding of file
import pyproj
import regex as re

# save to csv
def to_csv(df,filename):
    path = r"C:/Users/lea/DigitalHumanities/msc/SpatialHum/project"
    full_path = f"{path}//{filename}"
    df.to_csv(full_path, index = False)

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def load_html_files(directory):
    html_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            html_files.append(os.path.join(directory, filename))
    return html_files # returns list of file paths

# extract table information of each memorial and add to dataframe
def extract_data(html_content):
    final_df = pd.DataFrame()
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find(string="Information on memorial").find_parent("table")
    contents = []
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols if ele is not None]
        if len(cols) > 1:
            contents.append([ele for ele in cols if ele])
    temp_df = pd.DataFrame(contents).transpose()
    temp_df = temp_df.drop(0).reset_index(drop=True)
    if temp_df.shape[1] > 1 and temp_df.iloc[0,1] is not None and temp_df.iloc[0,1].strip() != '': # any(contents[1]): #len(contents) > 1 and any(contents[1]):
        final_df = pd.concat([final_df, temp_df], axis=0, ignore_index=True)
        print("data added")
    else:
        print("skipped due to no content")
    return final_df

def scrape_multiple_pages(directory):
    html_files = load_html_files(directory)
    scraped_data = {}

    for filename in html_files:
        page_name = os.path.splitext(os.path.basename(filename))[0]
        # detect encoding
        detected_encoding = detect_encoding(filename)
        if detected_encoding is None:
            print(f"Unable to detect Encoding for {filename}, using UTF-8 as fallback")
            #detected_encoding = 'utf-8'
        # read content with detected encoding
        with open(filename, 'r', encoding = detected_encoding) as file:
            html_content = file.read()

        scraped_data[page_name] = extract_data(html_content)
        print(f"Processed {filename}")
    return scraped_data

def combine_dataframes(dict_of_df):
    all_colums = set()
    for df in dict_of_df.values():
        all_colums.update(df.columns)
    
    combined_df = pd.DataFrame(index=dict_of_df.keys(), columns=list(all_colums))
    for i, (key,df) in enumerate(dict_of_df.items()):
        if not df.empty:
            combined_df.iloc[i] = df.values
    return combined_df

def extract_coordinates(s):
    x_match = re.search(r'X: (\d+)', s)
    y_match = re.search(r'Y: (\d+)', s)
    x = int(x_match.group(1)) if x_match else None
    y = int(y_match.group(1)) if y_match else None
    return pd.Series({'X': x, 'Y': y})

final_results = scrape_multiple_pages(r'C:/Users/lea/DigitalHumanities/msc/SpatialHum/project/htmls_data_memorials')
combined_df = combine_dataframes(final_results)
memorials_df = combined_df.dropna(subset=[1], how='any')

# preprocess dataframe in order to transform coordinates
memorials_df[['X', 'Y']] = memorials_df['10'].apply(extract_coordinates)

# adjust coordinates (column 10)
irish_grid = pyproj.Proj('epsg:29902')
gps = pyproj.Proj('epsg:4326')
def irish_to_gps(easting, northing):
    x,y = pyproj.transform(irish_grid, gps, easting, northing)
    print('done')
    return x,y
# convert coordinates in dataframe and save in new columns gps_x and gps_y
memorials_df[['gps_x','gps_y']] = memorials_df.apply(
    lambda row: irish_to_gps(row['X'], row['Y']),
    axis=1,
    result_type='expand'
)

#memorials_df = memorials_df.rename(columns={
#    1:'id', 2:'title', 3:'commemorating', 4:'date_of_incident', 5:'description', 6:'inscription',
#    7:'address', 8:'location_guide', 9:'map_grid_ref', 11:'previous_location', 12:'nature',
#    13:'physical_type', 14:'physical_materials', 15:'setting', 16:'access', 17:'post_unveiling', 18:'commissioned_by',
#    19:'artist(s)', 20:'date_unveiled', 24:'comments'})
# memorials_df = memorials_df.drop(columns=[0, 10, 21, 22, 23, 25, 'X', 'Y'])

# if read from backup file:
memorials_df = memorials_df.rename(columns={
    '1':'id', '2':'title', '3':'commemorating', '4':'date_of_incident', '5':'description', '6':'inscription',
    '7':'address', '8':'location_guide', '9':'map_grid_ref', '11':'previous_location', '12':'nature',
    '13':'physical_type', '14':'physical_materials', '15':'setting', '16':'access', '17':'post_unveiling', '18':'commissioned_by',
    '19':'artist(s)', '20':'date_unveiled', '24':'comments'})
memorials_df = memorials_df.drop(columns=['0', '10', '21', '22', '23', '25', 'X', 'Y'])

to_csv(memorials_df, 'memorials.csv')