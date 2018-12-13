from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep, time
from re import compile, match, search
from sys import argv
from random import choice
import os
import json
################################################################################
# General Utilities
################################################################################

def scrollBottom(browser):
    print('Starting to scroll')
    oldSource = browser.page_source
    while True:
        sleep(3)
        print('Executing scroll script')
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        newSource = browser.page_source
        if newSource == oldSource:
            break
        oldSource = newSource
    print('Done scrolling')
################################################################################
# Index Page Main
################################################################################

def getTopicsFromScrapeage():
    fr = open('topic_urls.txt', mode='r')
    lines = fr.read().split('\n')
    topic_urls = []
    for line in lines:
        x = line.split('\t')
        topic_urls.append(x[len(x)-1])
    return topic_urls

# TODO: NBD Combine these 2 functions
def downloadIndexPage(browser, topic, num_pages=1):
    url = topic + '?share=1'
    try:
        browser.get(url)
    except:
        return "<html></html>"
    for page in range(num_pages):
        scrollBottom(browser)
        sleep(3)
    html_source = browser.page_source
    return html_source

def extractQuestionLinks(html_source, useCached=False):
    if useCached:
        fr = open('index.html' , mode='r')
        html_source = fr.read()
    soup = BeautifulSoup(html_source)
    links = []
    for i in soup.find_all('a', { "class" : "question_link" }):
        if len(i) >0 :
            link = i['href']
            try:
                links.append(link)
            except UnicodeEncodeError:
                pass
    return links

def extractAnswerLinks(html_source, useCached=False):
    if useCached:
        fr = open('index.html' , mode='r')
        html_source = fr.read()
    soup = BeautifulSoup(html_source)
    links = []
    for i in soup.findAll('a', {'class':'ui_qtext_more_link'}):
        if len(i) >0 :
            link = i['href']
            try:
                links.append(link)
            except UnicodeEncodeError:
                pass
    return links

def getQuestionText(soup):
    try:
        a = soup.find('div', { "class" : "question_text_edit" }).getText()
        return a
    except:
        return None

def getTopics(soup):
    topics = soup.find_all('div', { "class" : "QuestionTopicListItem TopicListItem topic_pill" })
    return ', '.join(topic.getText() for topic in topics)


def getAnswerText(answer):
    # import pdb; pdb.set_trace()
    # answer_text = answer.find('div', { "class" : "ExpandedQText ExpandedAnswer" })
    answer_text = answer.find('div',{'class':'ui_qtext_expanded'})
    result = answer_text.getText()
    if result:
        return result

################################################################################
# Question Page Main
################################################################################
def answer(browser, answer_url):
    if not match('/', answer_url):
        print('Bad question url:', answer_url)
        return
    url = 'http://www.quora.com' + answer_url + '?share=1'
    browser.get(url)
    scrollBottom(browser)
    sleep(3)
    html_source = browser.page_source.encode('utf-8')
    
    soup = BeautifulSoup(html_source)
    content = ""
    for p in soup.findAll('p', {'class':'ui_qtext_para'}):
        try:
            content += p.text.strip()
        except Exception as e:
            pass
    return content

def question(browser, question_url):
    if not match('/', question_url):
        print('Bad question url:', question_url)
        return
    url = 'http://www.quora.com' + question_url + '?share=1'
    browser.get(url)
    scrollBottom(browser)
    sleep(3)
    html_source = browser.page_source.encode('utf-8')
    
    soup = BeautifulSoup(html_source)
    question_text = getQuestionText(soup)
    if question_text == None:
        return 0
    topics = getTopics(soup)
    collapsed_answer_pattern = compile('\d+ Answers? Collapsed')
    answers = soup.find_all('div', { "class" : "Answer AnswerBase" })  #class="Answer AnswerBase
    i = 1
    answer_text = ""
    for answer in answers:
        result = collapsed_answer_pattern.match(answer.getText())
        if result or 'add_answer_wrapper' in answer['class']:
            continue # skip collapsed answers and answer text box
        answer= getAnswerText(answer)
        answer_text = answer_text + answer
    try:
        dict= {'topics': topics, 'question': question_text, 'answers':answer_text}

    except UnicodeDecodeError:
        print('Unicode decode error')
        return 0
    #append this dict to previous dict in our answers file
    a = []
    if not os.path.isfile('answers.csv'):
        a.append(dict)
        with open ('answers.csv', 'w')as f:
            f.write(json.dumps(a,indent=2))
    else:
        with open ('answers.csv') as file:
            feeds = json.load(file)
        feeds.append(dict)
        with open('answers.csv', mode= 'w') as f:
            f.write(json.dumps(feeds,indent=2))

def answer_of_question(browser, question_url):
    if not match('/', question_url):
        print('Bad question url:', question_url)
        return
    url = 'http://www.quora.com' + question_url + '?share=1'
    browser.get(url)

    scrollBottom(browser)
    sleep(3)

    html_source = browser.page_source.encode('utf-8')
    
    soup = BeautifulSoup(html_source)
    
    answer_content_list = []

    collapsed_answer_pattern = compile('\d+ Answers? Collapsed')
    answers = soup.find_all('div', { "class" : "Answer AnswerBase" })  #class="Answer AnswerBase
    for answer in answers:
        result = collapsed_answer_pattern.match(answer.getText())
        if result or 'add_answer_wrapper' in answer['class']:
            continue # skip collapsed answers and answer text box
        answer_content = getAnswerText(answer)
        answer_content_list.append(answer_content)
    
    return answer_content_list

################################################################################
# Main
################################################################################

def main(argv):

    options = webdriver.ChromeOptions()
    options.binary_location='/usr/bin/google-chrome-stable'
    options.add_argument('--headless')
    options.add_argument('--start-maximized') 
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('window-size={}x{}'.format(*self.window_size))                                                                                                                                                                                                                                                                          
    browser = webdriver.Chrome(chrome_options=options, executable_path='./chromedriver_linux')  

    chromedriver = "./chromedriver_linux"
    os.environ["webdriver.chrome.driver"] = chromedriver
    start = time()
    option = argv

    if option == 'getquestionlinks':
        # browser = webdriver.Chrome(chromedriver)
        topic_urls = getTopicsFromScrapeage()
        
        num_pages = 20
        topic_questions_dict_filepath = './topic_question_answers.json'
        if os.path.isfile(topic_questions_dict_filepath):
            topic_questions_dict = json.load(open(topic_questions_dict_filepath,'r'))
        else:
            topic_questions_dict = {}
        for topic_url in topic_urls:
            num_answers = 0
            if topic_url not in topic_questions_dict:
                topic_questions_dict[topic_url] = {}
            try:
                html_source = downloadIndexPage(browser, topic_url,num_pages)
                links = extractQuestionLinks(html_source, False)
                answer_content_list = []
                for link in links:
                    if link in topic_questions_dict[topic_url]:
                        print('question {} has {} answers skip'.format(link, len(topic_questions_dict[topic_url][link])))
                        continue
                    else:
                        answer_content_list = answer_of_question(browser, link)
                        topic_questions_dict[topic_url][link] = answer_content_list
                        print('question {} has cralwed {} answers'.format(link, len(topic_questions_dict[topic_url][link])))
                        json.dump(topic_questions_dict, open(topic_questions_dict_filepath,'w'))
                        num_answers += len(topic_questions_dict[topic_url][link])
                print('Success when crawl {}, got {} answers'.format(topic_url, num_answers))

            except Exception as e:
                print('Error when crawl {}\n err_msg: {}'.format(topic_url, str(e)))

    elif option == 'downloadquestions':
        browser = webdriver.Chrome(chromedriver)
        links = []
        done = []
        with open('questions.txt', mode='r') as file:
            links = file.read().split('\n')
        try:
            with open('questions-done.txt', mode='r') as file:
                done = file.read().split('\n')
        except IOError:
            done = []
        links_set = set(links)
        done_set = set(done)
        
        links_not_done_unique = list(links_set.difference(done_set))
        print(len(links_not_done_unique), 'remaining')
        for link in links_not_done_unique:
            print(link)
            res = question(browser, link)
            if res != 0:
                with open('questions-done.txt', mode='a') as file:
                    try:
                        file.write((link + '\n').encode('utf-8'))
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        print('An encoding problem occured')
    elif option == 'getanswerlinks':
        browser = webdriver.Chrome(chromedriver)
        topic_urls = getTopicsFromScrapeage()
        
        num_pages = 10
        topic_answers_dict_filepath = './topic_answers_links.json'
        if os.path.isfile(topic_answers_dict_filepath):
            topic_answers_dict = json.load(open(topic_answers_dict_filepath,'r'))
        else:
            topic_answers_dict = {}
        for topic_url in topic_urls:
            if topic_url in topic_answers_dict:
                print('{}:{} crawled, skip'.format(topic_url, len(topic_answers_dict[topic_url])))
                continue
            try:
                html_source = downloadIndexPage(browser, topic_url,num_pages)
                links = extractAnswerLinks(html_source, False)
                topic_answers_dict[topic_url] = links
                json.dump(topic_answers_dict, open(topic_answers_dict_filepath,'w'))
                print('Success when crawl {}, got {} answers'.format(topic_url, len(links)))
            except Exception as e:
                print('Error when crawl {}\n err_msg: {}'.format(topic_url, str(e)))
    elif option == 'getanswercontent':
        browser = webdriver.Chrome(chromedriver)
        topic_answers_dict_filepath = './topic_answers_links.json'
        topic_answers_dict = json.load(open(topic_answers_dict_filepath,'r'))
        topic_answers_content_filepath = './topic_answers_content.json'
        if os.path.isfile(topic_answers_content_filepath):
            topic_answers_content_dict = json.load(open(topic_answers_content_filepath,'r'))
        else:
            topic_answers_content_dict = {}

        for topic_url in topic_answers_dict:
            if topic_url not in topic_answers_content_dict:
                topic_answers_content_dict[topic_url] = {}
            for answer_link in topic_answers_dict[topic_url]:
                if answer_link in topic_answers_content_dict[topic_url]:
                    print('topic:{} answer:{} crawled, skip'.format(topic_url, answer_link))
                    continue
                try:
                    answer_content = answer(browser, answer_link)
                    topic_answers_content_dict[topic_url][answer_link] = answer_content
                    json.dump(topic_answers_content_dict, open(topic_answers_content_filepath,'w'))
                    print('Success when crawl answer {}, got {}'.format(answer_link, len(answer_content)))
                except Exception as e:
                    print('Error when crawl {}\n err_msg: {}'.format(answer_link, str(e)))
    end = time()
    print('Script runtime: ', end - start)

if __name__ == "__main__":
    main(argv= "getquestionlinks")
    # main(argv= "getanswercontent")
