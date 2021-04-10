import requests
import csv
import urllib
import time
from bs4 import BeautifulSoup
from googlesearch import search


def str_cleaner(dirty_string):
    clean_string = dirty_string.replace(',', '')
    clean_string = clean_string.replace('„', '')
    return clean_string


def get_title(imdb_id):
    query = "https://www.imdb.com/title/" + imdb_id
    html_text = requests.get(query, headers={"accept-language": "en-US"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    # title = soup.find_all('title', limit=1)
    title_words = soup.title.contents[0].split()
    # year = int(title_words[-3][1:-1])
    title = ""
    for i in range(len(title_words) - 3):
        if(i == 0):
            title += title_words[i]
        else:
            title += " " + title_words[i]
    # print(year)
    # print(title)
    # print(title_words)

    return title


def simple_word_compare(word1, word2):
    word1 = word1.lower()
    word2 = word2.lower()
    score = 0.0
    for i in range(len(word1)):
        if i < len(word2) and word1[i] == word2[i]:
            score += 1.0
        else:
            break
    score = score / len(word1)
    return score


def simple_str_compare(string1, string2):
    words1 = string1.split()
    words2 = string2.split()
    score = 0.0
    for word in words1:
        local_score = 0.0
        for other_word in words2:
            temp_score = simple_word_compare(word, other_word)
            if temp_score > local_score:
                local_score = temp_score
        score += local_score

    score = score / len(words1)
    return score


def word_match(word1, word2):
    score = simple_word_compare(word1, word2)
    return score == 1.0


def str_compare_word_match(string1, string2):
    words1 = string1.split()
    words2 = string2.split()
    score = 0.0
    for word in words1:
        for other_word in words2:
            if word_match(word, other_word):
                score += 1.0
                break

    score = score / len(words1)
    return score


def concatenate_words(word_list, inf_lim, sup_lim):
    res = ""
    for i in range(max(0, inf_lim), min(sup_lim + 1, len(word_list))):
        if i == max(0, inf_lim):
            res += word_list[i]
        else:
            res += " " + word_list[i]
    return res


def get_imdb_id_duckduckgo_scraping(movie_title):
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "https://www.google.pt/search?q=" + \
        movie_title + "+site%3Aimdb.com%2Ftitle"
    html_text = requests.get(query, headers={
                             "accept-language": "en-US", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    top_result = soup.body.find('div', {"class": "g"})
    return top_result


def get_imdb_id_google_api(movie_title):
    movie_title = urllib.parse.quote_plus(movie_title + " movie")
    key = "AIzaSyDAuCR5quV01QZU0_F0GDx9fYFbs0fIIFI"
    cx = "8b8e8d84ef824d62e"
    url = "https://www.googleapis.com/customsearch/v1/siterestrict?key=" + \
        key + "&cx=" + cx + "&q=" + movie_title + "&num=1"
    response = requests.get(url)
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None
    result = response.json()
    if "items" not in result.keys():
        return None
    movie_link = result["items"][0]["link"]
    movie_id = movie_link[movie_link.find("/title")+7:]
    movie_id = movie_id[:movie_id.find("/")]
    return movie_id


def get_imdb_id_google_scraping(movie_title):
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "https://www.google.com/search?q=" + \
        movie_title + "+site%3Aimdb.com%2Ftitle"
    html_text = requests.get(query, headers={
                             "accept-language": "en-US", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    top_result = soup.body.find('div', {"class": "g"})
    return top_result


def get_imdb_id_google(movie_title):
    query = movie_title + " site:imdb.com"

    for j in search(query, tld="com", lang='en', num=1, stop=1):
        first_index = j.find("/title")
        title_id = j[first_index+7:]
        temp = title_id.find("/")
        title_id = title_id[:temp]

        return title_id

    return None


def get_imdb_id_tmdb_api(movie_title):
    movie_title = urllib.parse.quote_plus(movie_title)
    api_key = "1aab7ffe316d9a2f462ca84d49d9514c"
    url = "https://api.themoviedb.org/3/search/movie?api_key=" + api_key + \
        "&language=en-US&query=" + movie_title + "&page=1&include_adult=true"
    response = requests.get(url)
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None
    result = response.json()
    if result["total_results"] == 0:
        return None
    movie_id = result["results"][0]["id"]

    url = "https://api.themoviedb.org/3/movie/" + \
        str(movie_id) + "/external_ids?api_key=" + api_key
    response = requests.get(url)
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None

    result = response.json()
    if "imdb_id" not in result.keys():
        return None
    movie_id = result["imdb_id"]
    return movie_id


def get_imdb_id_omdb_api(movie_title):
    movie_title = urllib.parse.quote_plus(movie_title)
    apikey = "d05398fd"
    url = "http://www.omdbapi.com/?apikey=" + \
        apikey + "&s=" + movie_title + "&type=movie"
    response = requests.get(url)
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None
    result = response.json()
    if result["Response"] != "True":
        return None
    movie_id = result["Search"][0]["imdbID"]
    return movie_id


# if date = 1 -> gets the original (older) | if date = 2 -> gets the most recent one | any other date gets the first to appear in the search
def get_imdb_id(movie_title, date, repeat, tolerance):
    movie_title = str_cleaner(movie_title)
    # print(movie_title)
    og_title = movie_title
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "http://www.imdb.com/find?q=" + \
        movie_title + "&s=tt&ttype=ft&ref_=fn_ft"
    response = requests.get(query, headers={"accept-language": "en-US"})
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None
    html_text = response.text
    soup = BeautifulSoup(html_text, 'html.parser')
    result_table = soup.find('table', {"class": "findList"})

    if result_table is None:
        # print("Another One")
        if repeat:
            title_list = og_title.split()
            title_size = len(title_list)
            max_cut = (title_size - 1) // 2
            # print(title_list)
            imdb_id_list = []
            scores_list = []
            for i in range(max_cut):
                t_first = concatenate_words(title_list, max_cut, title_size)
                t_last = concatenate_words(title_list, 0, title_size - max_cut)
                t_both = concatenate_words(
                    title_list, max_cut, title_size - max_cut)
                id_first = get_imdb_id(t_first, date, False, tolerance)
                if id_first is not None:
                    fscore = str_compare_word_match(
                        get_title(id_first), t_first)
                    # print(fscore)
                    if fscore == 1 or fscore >= tolerance:
                        return id_first
                    imdb_id_list.append(id_first)
                    scores_list.append(fscore)
                id_last = get_imdb_id(t_last, date, False, tolerance)
                if id_last is not None:
                    lscore = str_compare_word_match(get_title(id_last), t_last)
                    # print(lscore)
                    if lscore == 1 or lscore >= tolerance:
                        return id_last
                    imdb_id_list.append(id_last)
                    scores_list.append(lscore)
                id_both = get_imdb_id(t_both, date, False, tolerance)
                if id_both is not None:
                    bscore = str_compare_word_match(get_title(id_both), t_both)
                    # print(bscore)
                    if bscore == 1 or bscore >= tolerance:
                        return id_both
                    imdb_id_list.append(id_both)
                    scores_list.append(bscore)

            unsure_id = None
            best_score = -1.0
            print(imdb_id_list)
            print(scores_list)

            if len(imdb_id_list) == 0:
                temp_id = ""
                temp_score = 0.0
                for word in title_list:
                    temp_id = get_imdb_id(word, date, False, tolerance)
                    if temp_id is not None:
                        imdb_id_list.append(temp_id)
                        temp_score = simple_word_compare(
                            get_title(temp_id), word)
                        scores_list.append(temp_score)
                for i in range(len(imdb_id_list)):
                    print(get_title(imdb_id_list[i]))
                    if (scores_list[i] > best_score):
                        best_score = scores_list[i]
                        unsure_id = imdb_id_list[i]
                return unsure_id
            else:
                for i in range(len(imdb_id_list)):
                    print(get_title(imdb_id_list[i]))
                    if (scores_list[i] > best_score):
                        best_score = scores_list[i]
                        unsure_id = imdb_id_list[i]
                return unsure_id

        return None

    results = result_table.find_all('tr')
    # print(len(results))
    id = results[0].find_all('td')[1].a['href'][7:-1]
    title = results[0].find_all('td')[1].a.contents[0]
    year = results[0].find_all('td')[1].contents[2][2:-2]
    # print("0-> " + title + " -> " + year)
    if date == 1 or date == 2:
        it = 1
        while True:
            if(it >= len(results)):
                break
            it_title = results[it].find_all('td')[1].a.contents[0]
            # print(str(iterator) + "-> " + it_title)
            if it_title == title:
                it_year = results[it].find_all('td')[1].contents[2][2:-2]
                # print(str(it) + "-> " + it_title + " -> " + it_year)
                if date == 1 and int(it_year) < int(year):
                    title = it_title
                    year = it_year
                    id = results[it].find_all('td')[1].a['href'][7:-1]
                if date == 2 and int(it_year) > int(year):
                    title = it_title
                    year = it_year
                    id = results[it].find_all('td')[1].a['href'][7:-1]

                it += 1
            else:
                break
    # print(id)
    # print(title)
    # print(year)
    return id


in_filename = "mismatched_titles_sample.csv"
out_filename = "matched_titles.csv"

with open(in_filename, newline='') as in_file:
    with open(out_filename, 'w', newline='') as out_file:
        reader = csv.reader(in_file)
        writer = csv.writer(out_file)
        start_time = time.time()
        num_processed = 0
        for title in reader:
            print("Processing title " + title[0])
            writer.writerow([get_imdb_id_omdb_api(title[0]), title[0]])
            num_processed += 1
        end_time = time.time()
        elapsed_time = end_time - start_time
        avg_time = elapsed_time/num_processed
        print("Processed " + str(num_processed) + "titles in " +
              str(elapsed_time) + "s" + "(average " + str(avg_time) + "s/title)")

print("Resulting matches saved to " + out_filename)


# print(get_imdb_id_google_scraping("The Lion King"))
