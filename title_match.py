import requests
import csv
import urllib
import time
from bs4 import BeautifulSoup
from googlesearch import search

def get_imdb_id_google(movie_title):
    query = movie_title + " site:imdb.com"

    for j in search(query, tld="com", lang='en', num=1, stop=1):
        first_index = j.find("/title")
        title_id = j[first_index+7:]
        temp = title_id.find("/")
        title_id = title_id[:temp]

        return title_id
    
    return None

#if date = 1 -> gets the original (older) | if date = 2 -> gets the most recent one | any other date gets the first to appear in the search
def get_imdb_id(movie_title, date=0):
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "http://www.imdb.com/find?q=" + movie_title + "&s=tt&ttype=ft&ref_=fn_ft"
    html_text = requests.get(query, headers={"accept-language": "en-US"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    result_table = soup.find('table', {"class": "findList"})

    if result_table is None:
        return None
    
    results = result_table.find_all('tr')
    id = results[0].find_all('td')[1].a['href'][7:-1]
    title = results[0].find_all('td')[1].a.contents[0]
    year = results[0].find_all('td')[1].contents[2][2:-2]
    if date == 1 or date == 2:
        it = 1
        while True:
            if(it >= len(results)):
                break
            it_title = results[it].find_all('td')[1].a.contents[0]
            if it_title == title:
                it_year = results[it].find_all('td')[1].contents[2][2:-2]
                if date == 1 and int(it_year) < int(year) :
                    title = it_title
                    year = it_year
                    id = results[it].find_all('td')[1].a['href'][7:-1]
                if date == 2 and int(it_year) > int(year) :
                    title = it_title
                    year = it_year
                    id = results[it].find_all('td')[1].a['href'][7:-1]

                it += 1
            else:
                break
    return id

in_filename = "mismatched_titles_sample.csv"
out_filename = "matched_titles.csv"

with open(in_filename, newline='') as in_file:
    with open(out_filename, 'w', newline='') as out_file:
        reader = csv.reader(in_file)
        writer = csv.writer(out_file)
        for title in reader:
            print("Processing title " + title[0])
            writer.writerow([get_imdb_id(title[0]), title[0]])
        print ("Resulting matches saved to " + out_filename)
