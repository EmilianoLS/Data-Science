from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import logging
import pickle
import os
import numpy as np

class LinkedInBot:
    def __init__(self, delay=5):
        if not os.path.exists("data"):
            os.makedirs("data")
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        self.delay=delay
        logging.info("Starting driver")
        self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def login(self, email, password):
        """Go to linkedin and login"""
        # go to linkedin:
        logging.info("Logging in")
        self.driver.maximize_window()
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(self.delay)

        self.driver.find_element('id','username').send_keys(email)
        self.driver.find_element('id','password').send_keys(password)

        self.driver.find_element('id','password').send_keys(Keys.RETURN)
        time.sleep(self.delay)

    def save_cookie(self, path):
        with open(path, 'wb') as filehandler:
            pickle.dump(self.driver.get_cookies(), filehandler)

    def load_cookie(self, path):
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def search_linkedin(self, keywords, location):
        """Enter keywords into search bar
        """
        logging.info("Searching jobs page")
        self.driver.get("https://www.linkedin.com/jobs/")
        # search based on keywords and location and hit enter
        self.wait_for_element_ready(By.CLASS_NAME, 'jobs-search-box__text-input')
        time.sleep(self.delay)
        search_bars = self.driver.find_elements(By.CLASS_NAME, 'jobs-search-box__text-input')
        search_keywords = search_bars[0]
        search_keywords.send_keys(keywords)
        time.sleep(self.delay)
        search_location = search_bars[3]
        time.sleep(self.delay)
        search_location.send_keys(location)
        time.sleep(self.delay)
        search_location.send_keys(Keys.RETURN)
        logging.info("Keyword search successful")
        time.sleep(self.delay)
    
    def wait(self, t_delay=None):
        """Just easier to build this in here.
        Parameters
        ----------
        t_delay [optional] : int
            seconds to wait.
        """
        delay = self.delay if t_delay == None else t_delay
        time.sleep(delay)

    #def scroll_to(self, job_list_item, jobs_link, i):
    def scroll_to(self, job_list_item):
        """Just a function that will scroll to the list item in the column 
        """
        self.driver.execute_script("arguments[0].scrollIntoView();", job_list_item)
        time.sleep(self.delay)
    
    def get_position_data(self, job):
        """Gets the position data for a posting.
        Parameters
        ----------
        job : Selenium webelement
        Returns
        -------
        list of strings : [position, company, location, details]
        """
        try:
            position = job.text.split('\n')[0]
        except:
            position = np.nan
        try:
            company = job.text.split('\n')[1]
        except:
            company = np.nan
        try:
            location = job.text.split('\n')[2]
        except:
            location = np.nan
        try:
            details = self.driver.find_element('id', "job-details").text
        except:
            details = np.nan
        return [position, company, location, details]

    def wait_for_element_ready(self, by, text):
        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((by, text)))
        except TimeoutException:
            logging.debug("wait_for_element_ready TimeoutException")
            pass

    def close_session(self):
        """This function closes the actual session"""
        logging.info("Closing session")
        self.driver.close()

    def run(self, email, password, keywords, location):
        if os.path.exists("data/cookies.txt"):
            self.driver.get("https://www.linkedin.com/")
            self.load_cookie("data/cookies.txt")
            self.driver.get("https://www.linkedin.com/")
        else:
            self.login(
                email=email,
                password=password
            )
            self.save_cookie("data/cookies.txt")

        logging.info("Begin linkedin keyword search")
        self.search_linkedin(keywords, location)
        self.wait()

        # scrape pages,only do first 8 pages since after that the data isn't 
        # well suited for me anyways:  
        self.position_list = []
        self.company_list = []
        self.location_list = []
        self.details_list = []
        

        for page in range(2, 8):
            self.jobs_link = []
            # get the jobs list items to scroll through:
            logging.info("Getting Jobs")
            #jobs_link = self.driver.find_elements(By.CLASS_NAME, "job-card-list__title") # Encuentra los links que esten a la vista en la pagina
            #self.links_de_trabajos = len(jobs_link)
            jobs_container = self.driver.find_elements(By.CLASS_NAME, "occludable-update") # Encuentra todas las ofertas de la pagina (25)
            for i in jobs_container[:-1]:
            #for job,i,container in zip(jobs_link, range(0, len(jobs_link)), jobs_container[0:len(jobs_link)]):
                self.scroll_to(i)
                self.jobs_link.append(self.driver.find_elements(By.CLASS_NAME, "job-card-list__title"))
                #jobs_link[i].click()
                #time.sleep(self.delay)
                #job_detail = self.driver.find_element(By.CLASS_NAME, "jobs-search__job-details")
                #self.job_details = job_detail.text.split('\n')
                #print(self.job_detail.text.split('\n'))
                #descriptions = self.get_position_data(container)    
                #self.position_list.append(descriptions[0])
                #self.company_list.append(descriptions[1])
                #self.location_list.append(descriptions[2])
                #self.details_list.append(descriptions[3])
                 
            final_list = set()
            for element in range(0, len(self.jobs_link)):
                for i in range(0, len(self.jobs_link[element])):
                    final_list.add(self.jobs_link[element][i])
            
            final_list = list(final_list)
            
            for i, container in zip(range(0, len(final_list)), jobs_container[0:len(final_list)]):
                final_list[i].click()
                time.sleep(self.delay)
                descriptions = self.get_position_data(container)
                self.position_list.append(descriptions[0])
                self.company_list.append(descriptions[1])
                self.location_list.append(descriptions[2])
                self.details_list.append(descriptions[3]) 
            # go to next page:
            self.driver.find_element(By.XPATH, f"//button[@aria-label='Page {page}']").click()
            self.wait()
        logging.info("Done scraping.")
        logging.info("Closing DB connection.")
        self.close_session()