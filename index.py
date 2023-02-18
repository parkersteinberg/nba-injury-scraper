from scrape_injury_data import scrape_injuries
from data_to_sql import data_to_sql
from create_injury_logs import create_injury_logs

if __name__ == '__main__':
  # run things!
  # scrape injury data
  injury_df = scrape_injuries()
  # export to injuries table in SQL db
  data_to_sql(injury_df)
  # pull data from injuries table and create injury_logs
  create_injury_logs()