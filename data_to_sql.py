### Importing data to SQL 

import os
import psycopg2
from sqlalchemy import create_engine, text
from scrape_injury_data import scrape_injuries

# get injury_df from nba_injury_scraper

def data_to_sql(injury_df):

  engine = create_engine(os.environ["DATABASE_URL"])
  conn = engine.connect()

  res = conn.execute(text("SELECT now()")).fetchall()
  print(res)

  injury_df.to_sql('injuries', con=engine, 
                  #  if_exists='replace'
                  )