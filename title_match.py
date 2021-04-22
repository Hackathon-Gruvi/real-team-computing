import requests
from bs4 import BeautifulSoup
import urllib
import csv
from googlesearch import search
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import config


def test_len(search, result, tolerance):
    if tolerance > 1:
        tolerance = 1
    if tolerance < 0:
        tolerance = 0
    biggest_case = tolerance + 1
    smallest_case = 1 - tolerance
    return len(result) <= len(search) * biggest_case and len(result) >= len(search) * smallest_case


def test_numbers(search, result):
    snumbers = []
    rnumbers = []
    for char in search:
        if char >= '0' and char <= '9':
            snumbers.append(char)
    for char in result:
        if char >= '0' and char <= '9':
            rnumbers.append(char)
    return snumbers == rnumbers


def test_words(search, result, minlen):
    return str_compare_word_match(result, search, minlen) == 1.0


def test_exactmatch(search, result):
    return search == result


def run_all_tests(search, result, fall_back_used, tolerance, minlen):
    if test_exactmatch(search, result):
        return "COMP"
    test_result = "----"
    if not fall_back_used:
        test_result = "F---"
    if test_numbers(search, result):
        test_result = test_result[0] + "N--"
    if test_words(search, result, minlen):
        test_result = test_result[0:2] + "W-"
    if test_len(search, result, tolerance):
        test_result = test_result[0:3] + "L"

    return test_result


def test_score_converter(str_test_result):
    score = 0
    if str_test_result == "COMP":
        score = 100
    else:
        if str_test_result[0] == 'F':
            score += 40
        if str_test_result[1] == 'N':
            score += 25
        if str_test_result[2] == 'W':
            score += 25
        if str_test_result[3] == 'L':
            score += 5
    return score


def test_compare(test_result, other_test_result):
    score = test_score_converter(test_result)
    other_score = test_score_converter(other_test_result)
    return other_score > score


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


def run_all_tests_id(search, result_id, fall_back_used, tolerance, minlen):
    result_title = get_title(result_id)
    run_all_tests(search, result_title, fall_back_used, tolerance, minlen)


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


def str_compare_word_match(string1, string2, minlen):
    words1 = string1.split()
    words2 = string2.split()
    score = 0.0
    counter = 0.0
    for word in words1:
        if len(word) >= minlen:
            counter += 1.0
            for other_word in words2:
                if word_match(word, other_word):
                    score += 1.0
                    break

    if counter > 0.0:
        score = score / counter
    else:
        score = 1.0
    return score


def concatenate_words(word_list, inf_lim, sup_lim):
    res = ""
    for i in range(max(0, inf_lim), min(sup_lim + 1, len(word_list))):
        if i == max(0, inf_lim):
            res += word_list[i]
        else:
            res += " " + word_list[i]
    return res

# NOT IN USE AND NOT DONE


def get_imdb_id_duckduckgo_scraping(movie_title, date):
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "https://www.google.pt/search?q=" + \
        movie_title + "+site%3Aimdb.com%2Ftitle"
    html_text = requests.get(query, headers={
                             "accept-language": "en-US", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    top_result = soup.body.find('div', {"class": "g"})
    return top_result


def get_imdb_id_google_api(movie_title, date=0):
    movie_title = urllib.parse.quote_plus(movie_title + " movie")
    cx = "8b8e8d84ef824d62e"
    url = "https://www.googleapis.com/customsearch/v1/siterestrict?key=" + \
        config.google_api_key + "&cx=" + cx + "&q=" + movie_title + "&num=1"
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

# NOT IN USE AND NOT DONE


def get_imdb_id_google_scraping(movie_title, date=0):
    movie_title = urllib.parse.quote_plus(movie_title)
    query = "https://www.google.com/search?q=" + \
        movie_title + "+site%3Aimdb.com%2Ftitle"
    html_text = requests.get(query, headers={
                             "accept-language": "en-US", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"}).text
    soup = BeautifulSoup(html_text, 'html.parser')
    top_result = soup.body.find('div', {"class": "g"})
    return top_result

# NOT IN USE


def get_imdb_id_google(movie_title, date):
    query = movie_title + " site:imdb.com"

    for j in search(query, tld="com", lang='en', num=1, stop=1):
        first_index = j.find("/title")
        title_id = j[first_index+7:]
        temp = title_id.find("/")
        title_id = title_id[:temp]

        return title_id

    return None


def get_imdb_id_tmdb_api(movie_title, date=0):
    movie_title = urllib.parse.quote_plus(movie_title)
    url = "https://api.themoviedb.org/3/search/movie?api_key=" + config.tmdb_api_key + \
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
        str(movie_id) + "/external_ids?api_key=" + config.tmdb_api_key
    response = requests.get(url)
    if response.status_code != 200:
        print("HTTP Status " + str(response.status_code))
        return None

    result = response.json()
    if "imdb_id" not in result.keys():
        return None
    movie_id = result["imdb_id"]
    return movie_id


def get_imdb_id_omdb_api(movie_title, date=0):
    movie_title = urllib.parse.quote_plus(movie_title)
    url = "http://www.omdbapi.com/?apikey=" + \
        config.omdb_api_key + "&s=" + movie_title + "&type=movie"
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
def get_imdb_id_imdb(movie_title, date=0):
    movie_title = str_cleaner(movie_title)
    # print(movie_title)
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


def despair(get_id, movie_title, date=0, tolerance=0.75):
    title_list = movie_title.split()
    title_size = len(title_list)
    max_cut = (title_size - 1) // 2
    # print(title_list)
    imdb_id_list = []
    scores_list = []
    for i in range(max_cut):
        t_first = concatenate_words(title_list, max_cut, title_size)
        t_last = concatenate_words(title_list, 0, title_size - max_cut)
        t_both = concatenate_words(title_list, max_cut, title_size - max_cut)
        id_first = get_id(t_first, date)
        if id_first is not None:
            fscore = str_compare_word_match(get_title(id_first), t_first, 0)
            # print(fscore)
            if fscore == 1 or fscore >= tolerance:
                return id_first
            imdb_id_list.append(id_first)
            scores_list.append(fscore)
        id_last = get_id(t_last, date)
        if id_last is not None:
            lscore = str_compare_word_match(get_title(id_last), t_last, 0)
            # print(lscore)
            if lscore == 1 or lscore >= tolerance:
                return id_last
            imdb_id_list.append(id_last)
            scores_list.append(lscore)
        id_both = get_id(t_both, date)
        if id_both is not None:
            bscore = str_compare_word_match(get_title(id_both), t_both, 0)
            # print(bscore)
            if bscore == 1 or bscore >= tolerance:
                return id_both
            imdb_id_list.append(id_both)
            scores_list.append(bscore)
    unsure_id = None
    best_score = -1.0
    #print(imdb_id_list)
    #print(scores_list)
    if len(imdb_id_list) == 0:
        temp_id = ""
        temp_score = 0.0
        for word in title_list:
            temp_id = get_id(word, date)
            if temp_id is not None:
                imdb_id_list.append(temp_id)
                temp_score = simple_word_compare(
                    get_title(temp_id), word)
                scores_list.append(temp_score)
        for i in range(len(imdb_id_list)):
            #print(get_title(imdb_id_list[i]))
            if (scores_list[i] > best_score):
                best_score = scores_list[i]
                unsure_id = imdb_id_list[i]
        return unsure_id
    else:
        for i in range(len(imdb_id_list)):
            #print(get_title(imdb_id_list[i]))
            if (scores_list[i] > best_score):
                best_score = scores_list[i]
                unsure_id = imdb_id_list[i]
        return unsure_id


def generic_get_id(get_id, fall_back, clean, movie_title, date=0, tolerance=0.75):
    if clean:
        movie_title = str_cleaner(movie_title)
    movie_id = get_id(movie_title, date)
    if movie_id is None and fall_back:
        movie_id = despair(get_id, movie_title, date, tolerance)
    return movie_id


def get_titles_from_csv(in_filename):
    titles = []
    with open(in_filename, newline='') as in_file:
        reader = csv.reader(in_file)
        for title in reader:
            titles.append(title[0])
    return titles


in_filename = "mismatched_titles_sample.csv"
out_filename = "matched_titles.csv"


async def get_ids_asynchronous(titles):
    with ThreadPoolExecutor(max_workers=50) as executor:
        loop = asyncio.get_event_loop()

        date = 2
        tolerance = 0.75
        tasks = []
        for i in range(len(titles)):
            tasks.append(loop.run_in_executor(executor, generic_get_id,
                         *(get_imdb_id_imdb, True, True, titles[i], date, tolerance)))
        for i in range(len(titles)):
            tasks.append(loop.run_in_executor(executor, generic_get_id, *
                         (get_imdb_id_google_api, True, True, titles[i], date, tolerance)))
        for i in range(len(titles)):
            tasks.append(loop.run_in_executor(executor, generic_get_id, *
                         (get_imdb_id_tmdb_api, True, True, titles[i], date, tolerance)))
        for i in range(len(titles)):
            tasks.append(loop.run_in_executor(executor, generic_get_id, *
                         (get_imdb_id_omdb_api, True, True, titles[i], date, tolerance)))
        return await asyncio.gather(*tasks)

titles = get_titles_from_csv(in_filename)
loop = asyncio.get_event_loop()
print("Processing titles ...")
start_time = time.time()
future = asyncio.ensure_future(get_ids_asynchronous(titles))
result = loop.run_until_complete(future)
end_time = time.time()
elapsed_time = end_time - start_time
avg_time = elapsed_time/len(titles)
print("Processed " + str(len(titles)) + " titles in " +
      str(elapsed_time) + "s" + "(average " + str(avg_time) + "s/title)")
results = []
results.append(result[:len(titles)])
results.append(result[len(titles):2*len(titles)])
results.append(result[2*len(titles):3*len(titles)])
results.append(result[3*len(titles):4*len(titles)])

with open(out_filename, 'w', newline='') as out_file:
    writer = csv.writer(out_file)
    start_time = time.time()
    date = 2
    tolerance = 0.75
    writer.writerow(["Title", "IMDb", "Google", "TMDB", "OMDb"])
    for i in range(len(titles)):
        writer.writerow([titles[i], results[0][i], results[1]
                        [i], results[2][i], results[3][i]])

print("Resulting matches saved to " + out_filename)

"""
#Synchronous version
with open(out_filename, 'w', newline='') as out_file:
    writer = csv.writer(out_file)
    start_time = time.time()
    date = 2
    tolerance = 0.75
    writer.writerow(["Title", "IMDb", "Google", "TMDB", "OMDb"])
    for title in titles:
        print("Processing title " + title)
        movie_id_imdb = generic_get_id(get_imdb_id_imdb, True, True, title, date, tolerance)
        movie_id_google = generic_get_id(get_imdb_id_google_api, True, True, title, date, tolerance)
        movie_id_tmdb = generic_get_id(get_imdb_id_tmdb_api, True, True, title, date, tolerance)
        movie_id_omdb = generic_get_id(get_imdb_id_omdb_api, True, True, title, date, tolerance)
        writer.writerow([title, movie_id_imdb, movie_id_google, movie_id_tmdb, movie_id_omdb])
    end_time = time.time()
    elapsed_time = end_time - start_time
    avg_time = elapsed_time/len(titles)
    print("Processed " + str(len(titles)) + "titles in " +
            str(elapsed_time) + "s" + "(average " + str(avg_time) + "s/title)")

print("Resulting matches saved to " + out_filename)
"""

"""
print(run_all_tests("F9 Fast and Furious 9", "F9", False, 0.25, 4))
print(run_all_tests("Marvel Black Widow", "Black Widow", False, 0.25, 4))
print(run_all_tests("KÃTYRIT: GRUN TARINA", "Gru o Maldisposto 2", False, 0.25, 4))
print(run_all_tests("Tom y Jerry", "Tom & Jerry", False, 0.25, 4))
print(run_all_tests("Peter Rabbit", "Peter Rabbit 2: The Runaway", False, 0.25, 4))
print(run_all_tests("Full", "Full", False, 0.25, 4))
print(run_all_tests("Ainbo: Hrdinka pralesa", "Ainbo", False, 0.25, 4))
"""
