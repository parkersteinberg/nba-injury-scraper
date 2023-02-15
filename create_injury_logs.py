import os
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine, text

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
import time
from datetime import datetime


def create_injury_logs(start_date, save_csv=False):
  '''
  Reads new records from injury table and creates records in injury_logs table
  inputs: 
  - start_date: earliest date for entries from injury table to create logs from
  outputs: 
  - none (side effect)
  '''


  # OVERALL PROCESS: 

  # 1. read from SQL db into pandas 
  engine = create_engine(os.environ["DATABASE_URL"])
  conn = engine.connect()

  res = conn.execute(text("SELECT now()")).fetchall()
  print(res)# if prints, connection has been made

  query_date_string = f"SELECT * FROM injuries WHERE date >= '{start_date}'"
  raw_injuries = pd.read_sql(query_date_string, conn, parse_dates=["date"])

  # 2. get unique players and create "injury_logs" dataframe in pandas
    # this creates a unique row PER INJURY in a new pandas dataframe
    # also clean up the df, make sure date objects are correctly typed
  unique_players = np.unique(raw_injuries[['acquired', 'relinquished']].values)[1:]
  # create parent df that all new entries will go into 
  cols_injury_log = ['player', 
                    'team',
                    'injury_reason', 
                    'date_placed', 
                    'date_activated', 
                    'out_for_season', 
                    'injury_duration', 
                    'games_missed']
  injury_logs = pd.DataFrame(columns=cols_injury_log)

  # iterate over unqiue players and add entries to 
  for i, player in enumerate(unique_players):
    
    player_df = raw_injuries.loc[(raw_injuries['acquired'] == player) | (raw_injuries['relinquished'] == player)]
    
    start_date = ''
    end_date = ''
    injury_reason = ''
    out_for_season = 0
    injury_duration = 0

    for index, row in player_df.iterrows():
        team = row['team']
        # if placed on IL, set start date and injury reason
        if row['relinquished']:
            print('ENTERING RELINQUISHED...')
            start_date = row['date']
            # TODO: only grab everything to right of 'placed on IL with'
            injury_reason = row['notes']

            # set out for season flag
            # if out for season is true, there is no activated?
            if 'out for season' in injury_reason:
                out_for_season = 1

                # ADD ROW TO LOGS TABLE (helper function for adding rows?)
                    # inputs: 1) object for passing into pd.Series
                    # and 2) df to add it to 
                injury_log_row = pd.Series({
                    'player': player, 
                    'team': team,
                    'injury_reason': injury_reason, 
                    'date_placed': start_date, 
                    'date_activated': end_date, 
                    'out_for_season': out_for_season, 
                    'injury_duration': injury_duration, 
                    'games_missed': None
                }) 
                # add player, start_date, end_date, out for season, and injury_reasons to df 
                injury_logs = pd.concat([injury_logs, injury_log_row.to_frame().T], ignore_index=True)

                # RESET ALL VALUES 
                start_date = ''
                end_date = ''
                injury_reason = ''
                out_for_season = 0
                injury_duration = 0

        # if end activated from IL, match is found and append to master df
        # we will only enter this conditional if out_for_season is 0
        if row['acquired'] and start_date:
            print('ENTERING ACQUIRED...')
            # get end date from current row 
            end_date = row['date']

            # get injury duration
            injury_duration = (end_date - start_date).days

            # create row to add to logs df 
            injury_log_row = pd.Series({
                'player': player, 
                'team': team,
                'injury_reason': injury_reason, 
                'date_placed': start_date, 
                'date_activated': end_date, 
                'out_for_season': out_for_season, 
                'injury_duration': injury_duration, 
                'games_missed': None
            }) 
            # add player, start_date, end_date, out for season, and injury_reasons to df 
            injury_logs = pd.concat([injury_logs, injury_log_row.to_frame().T], ignore_index=True)
            # injury_logs.append()

            # RESET ALL VALUES 
            start_date = ''
            end_date = ''
            injury_reason = ''
            out_for_season = 0
            injury_duration = 0

  # ** end of iterating over unique_players array and creating associated logs **

  # clean up dates and team names in injury logs
  injury_logs['date_placed'] = pd.to_datetime(injury_logs['date_placed'])

  # TODO: clean up data so that no non-existent teams are in db (e.g. Bobcats)
  # only a 1 time thing bc as we get new data in, there won't be any non-existent teams

  # 3. data to fill: games missed for all players + length of injury for end of season injuries
    # use NBA api to get games missed from date range of injury
  
  # for logging to console during runtime
  count = 1
  # for row in injury logs
  for index, row in injury_logs.iterrows():
      print('iteration number ', count)
      print('handling data for {0} on the {1}.......'.format(row['player'], row['team']))
      count += 1
      start_date = row['date_placed']
      # if out_for_season = 1
      if row['out_for_season'] == 1:
          print('found out for season, injury is:', row['injury_reason'])

          temp_team = row['team']
          year = start_date.year
          month = start_date.month
          # get season based on year + month of injury
          if month <= 7:
              season = year - 1
          else:
              season = year
          
          # get team id for player's team
          # TODO: update this logic so it's reset on every player 
          nba_teams = teams.get_teams()
          current_team = [team for team in nba_teams if temp_team in team['nickname'] or temp_team in team['full_name'] ]
          # handle errors, such as caused by "Bobcats" for team name, which don't exist anymore
          # if team is found 
          if len(current_team) > 0:
              current_team = current_team[0]
              current_team_id = current_team['id']

              gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=current_team_id)
              games = gamefinder.get_data_frames()[0]

              current_season_games = games[games.SEASON_ID.str[-4:] == str(season)]
              last_game_of_season = pd.to_datetime(current_season_games['GAME_DATE'].max(), format='%Y-%m-%d')

          # if team is not found from API
          # TODO: FIGURE OUT BEST OPTION HERE (leave out, cast as zero days?)
          else:
              # average last game of season is april 10th, is the best we have 
              last_game_of_season = pd.to_datetime(f'{season + 1}-04-10',  format='%Y-%m-%d')
              
          # update date_activated and injury_duration columns in injury_logs df
          injury_logs.loc[index, 'date_activated'] = last_game_of_season
          
          injury_duration = (last_game_of_season - start_date).days
          injury_logs.loc[index, 'injury_duration'] = injury_duration
          print("")
          
      # calculate number of games missed for the injury
      end_date = row['date_activated']
      
      gamefinder = leaguegamefinder.LeagueGameFinder(
          team_id_nullable=current_team_id
      )
      # may need a conditional statement here to make sure that games has more than 1 entry
      games = gamefinder.get_data_frames()[0]
      # convert date to date_time, get all games in range, then calculate total games
      games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'], format='%Y-%m-%d')
      games_in_range = games.loc[(games['GAME_DATE'] >= start_date) & (games['GAME_DATE'] < end_date)]
      games_missed = len(games_in_range)
      
      # add games missed to injury_log df
      injury_logs.loc[index, 'games_missed'] = games_missed

      # sleep to keep nba api happy (blocks if requests come more than every 0.6 sec)
      time.sleep(.600)



  # 4. add updated injury_logs (now with injury duration + games missed) to SQL db
    # optionally, save as csv 
  engine = create_engine(os.environ["DATABASE_URL"])
  conn = engine.connect()

  res = conn.execute(text("SELECT now()")).fetchall()
  print(res)
  injury_logs.to_sql('injury_logs', con=engine)
  # save to csv
  if save_csv:
    injury_logs.to_csv('injury_logs.csv', index=False)