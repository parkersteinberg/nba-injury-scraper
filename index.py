from scrape_injury_data import scrape_injuries
from data_to_sql import data_to_sql

if __name__ == 'main':
  # run things

  # run scarpe injuries
  injury_df = scrape_injuries()
  # export to injuries table in SQL db
  data_to_sql(injury_df)
  # pull data from injuries table and create injury_logs
  
  print('hello')