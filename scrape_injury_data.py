# imports
from bs4 import BeautifulSoup
import pandas as pd
import requests
# initialize df
injury_df = pd.DataFrame(columns=['date', 'team', 'acquired', 'relinquished', 'notes'])

def scrape_injuries():

  page = 0
  base_url = 'https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate=2012-10-01&EndDate=&ILChkBx=yes&Submit=Search&start=0'

  while page > -1:
      # set dynamic url
      url = f'https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate=2012-10-01&EndDate=&ILChkBx=yes&Submit=Search&start={page}'
      print('getting data from '+ url + "......")
      req = requests.get(url)
      soup = BeautifulSoup(req.content, 'html.parser')
      
      # if table does not exist (has 1 or fewer rows), break (end scraping)
      if len(soup.find('table', class_='datatable center').find_all('tr')) <= 1:
          break
      
      # do the scraping 
      # get table
      table = soup.find('table', class_='datatable center')
      # iterate over rows in table
      for row in table.find_all('tr', attrs={'align': 'left'}):
          # get columns
          columns = row.find_all('td')
          # save cells to variables
          date = columns[0].text
          team = columns[1].text[1:]
          acquired = columns[2].text[3:]
          relinquished = columns[3].text[3:]
          notes = columns[4].text
          # add data to injury dataframe
          new_row = pd.Series({
              'date': date,
              'team': team, 
              'acquired': acquired,
              'relinquished': relinquished, 
              'notes': notes
          })

          injury_df = pd.concat([injury_df, new_row.to_frame().T], ignore_index=True)
          
      
      page += 25

  return injury_df