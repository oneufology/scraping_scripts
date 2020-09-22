from datetime import datetime
from datetime import datetime, timedelta
import requests

from bs4 import BeautifulSoup
import pyodbc


def main():
    creds = get_creds()
    eod_user = get_user()
    start_date = get_stock_filedate(creds)
    dates_l = get_dates(start_date)
    download_file(eod_user, dates_l)


def get_creds():
    with open('PythonDB.txt', 'r') as f:
        server = f.readline().split('"')[1]
        database = f.readline().split('"')[1]
        username = f.readline().split('"')[1]
        password = f.readline().split('"')[1]
        return {
            'server': server,
            'db': database,
            'user': username,
            'pass': password,
        }


def get_user():
    with open('EODuser.txt', 'r') as user:
        username = user.readline().split('"')[1]
        password = user.readline().split('"')[1]
        return {
            'user': username,
            'pass': password,
        }


def get_stock_filedate(c):
    driver = '{ODBC Driver 13 for SQL Server}'
    cnxn = pyodbc.connect(f"DRIVER={driver};SERVER={c['server']};PORT=1433;DATABASE={c['db']};UID={c['user']};PWD={c['pass']}")
    cursor = cnxn.cursor()
    sql = """
    DECLARE @return_value int,
    @ReturnValue nvarchar(8)
    EXEC @return_value = [dbo].[spGetStockFileDate]
    @ReturnValue = @ReturnValue OUTPUT
    SELECT @ReturnValue as N'@ReturnValue'
    SELECT 'Return Value' = @return_value
    """
    cursor.execute(sql)
    return cursor.fetchone()[0]


def get_dates(start_date):
    dates_l = []
    start_date = datetime.strptime(start_date, '%Y%m%d').date()
    tomorrow = datetime.today().date() + timedelta(days=1)
    while start_date < tomorrow:
        start_date += timedelta(days=1)
        filedate = start_date.strftime('%Y%m%d')
        dates_l.append(filedate)
    return dates_l


def download_file(eod_user, dates_l):
    URL = 'http://xxxxxxx.com/download.aspx'
    session = requests.Session()
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    viewstate = soup.find(id='__VIEWSTATE')['value']
    generator = soup.find(id='__VIEWSTATEGENERATOR')['value']
    event_valid = soup.find(id='__EVENTVALIDATION')['value']
    ct100_tsm = soup.find(id='ctl00_tsm_HiddenField')['value']

    login_form = {
        'ctl00$cph1$ls1$txtEmail': eod_user['user'],
        'ctl00$cph1$ls1$txtPassword': eod_user['pass'],
        'ctl00$cph1$ls1$btnLogin': 'Login',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': generator,
        '__EVENTVALIDATION': event_valid,
        'ctl00_tsm_HiddenField': ct100_tsm,
    }

    session.post(URL, data=login_form)
    response = session.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    id = soup.select_one("a[href*=filedownload]")['href']
    id = id.split('k=')[1]
    id = id.split('&')[0]

    for symbol in ['NASDAQ', 'NYSE']:
        for date in dates_l:
            download_link = f"http://xxxxxxxx.com/data/filedownload.aspx?e={symbol}&sd={date}&ed={date}&d=1&k={id}&o=d&ea=1&p=0"
            file = session.post(download_link)
            file_len = file.headers['Content-Length']
            _dir = f"Data/Unprocessed/{symbol}_{date}.txt"

            if file_len != '0':
                with open(_dir, 'wb') as f:
                    f.write(file.content)
                    print(f"{symbol}_{date}")


if __name__ == '__main__':
    main()
