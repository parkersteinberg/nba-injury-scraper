# NBA Injury Data Scraper: 

## This repo is used to create the dataset used for [Injury Insights](https://github.com/parkersteinberg/nba-app)

<br>

### Data scraped from: [Pro Sports Transactions](https://www.prosportstransactions.com/basketball/Search/Search.php) (a great resource!)
### PostgreSQL db hosted with [CockroachDB](https://www.cockroachlabs.com/)

<br>

## Libraries / packages used
- [beautiful soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)
- [requests](https://pypi.org/project/requests/)
- [psycopg2](https://www.psycopg.org/docs/)
- [sqlachemy](https://www.sqlalchemy.org/)
- [PostgreSQL with Cockroach DB](https://www.cockroachlabs.com/)
- [nba_api](https://github.com/swar/nba_api)

<br>

## Setup
1. Set database URL environment variable
`export DATABASE_URL = <YOUR_URL>`
2. run index.py: `python3 index.py`
