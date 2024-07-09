from bs4 import BeautifulSoup
import requests
import selenium
from urllib.parse import urlsplit, urlunsplit
import re
import csv
import datetime


class PhdFinder:
    def __init__(self, url, weighted_kw, headers=None):
        self.url = url
        self.headers = headers
        self.search_page = requests.get(url, headers=headers)
        self.marks = [',', '.', ')', '(', '?', '"', ':', "'", "`", ';', '’']
        self.weighted_kw = weighted_kw
        split_url = urlsplit(url)
        self.base_url = split_url.scheme + "://" + split_url.netloc

    def parse_job(self, job):
        print('parse job')

    def add_jobs(self, jobs_list: list):
        print('add jobs')

    def remove_marks(self, desc_txt):
        for mark in self.marks:
            desc_txt = desc_txt.replace(mark, '')
        return desc_txt

    def score(self, desc_txt):
        rel_score = 0
        for kw, weight in self.weighted_kw:
            rel_score += len(re.findall(kw, desc_txt)) * weight
        return rel_score

    def get_full_url(self, sub_url):
        return self.base_url + sub_url

    @staticmethod
    def create_job_info(title_link, uni, deadline, score, link, country):
        job_info = dict()
        job_info['Title'] = title_link
        job_info['Country'] = country
        job_info['University'] = uni
        job_info['Deadline'] = deadline
        job_info['Priority'] = score
        job_info['Link'] = link
        return job_info

    @staticmethod
    def print_job_info(job_info: dict):
        for key in job_info.keys():
            print(f'{key}: {job_info[key]}')
        print('----------------------------------------')


class FindAPhd(PhdFinder):
    def __init__(self, url, weighted_kw, headers=None):
        super().__init__(url, weighted_kw, headers)

    def parse_job(self, job):
        title_link = job.find('a', class_='h4 text-dark mx-0 mb-3')
        inst_dep = job.find('div',
                            class_='instDeptRow phd-result__dept-inst align-items-center row mx-0 mb-3')
        inst_link = inst_dep.find('a', class_='instLink')
        # dep_link = inst_dep.find('a', class_='deptLink')
        desc_frag = job.find('div', class_='descFrag w-100')
        find_more_link = desc_frag.find('a')
        # supervisor = job.find('a', class_='super')
        more_info = job.find('div', class_='phd-icon-area mx-n1')
        more_info_els = more_info.find_all('a')
        deadline = 'NA'
        for mi_el in more_info_els:
            span_desc = mi_el.find('i')
            class_span = span_desc['class']
            if 'fa-calendar' in class_span:
                deadline = mi_el.text.strip()
                try:
                    deadline = datetime.datetime.strptime(deadline, '%d %B %Y').strftime('%m/%d/%y')
                except:
                    print(f'Wrong deadline: ' + deadline)
            # elif 'fa-graduation-cap' in class_span:
            #     job_type = mi_el.text
            # elif 'fa-wallet' in class_span:
            #     fund_type = mi_el.text

        rel_score = 0
        country = 'NA'
        job_details = requests.get(self.get_full_url(find_more_link['href']), headers=headers)
        if job_details.status_code == 200:
            job_details_txt = job_details.content
            job_details_bs = BeautifulSoup(job_details_txt, "html.parser")
            desc_el = job_details_bs.find('div', class_='phd-sections__content px-0 col-24')

            details_txt = desc_el.text.strip().lower()
            details_txt = self.remove_marks(details_txt)
            rel_score = self.score(details_txt)

            # Country and tags
            tags_container = job_details_bs.find('div', class_='phd-data__container')
            tag_links = tags_container.find_all('a', class_='phd-data')
            country = tag_links[1].text

        job_info = self.create_job_info(title_link.text.strip(),
                                        inst_link.text.strip(),
                                        deadline.strip(),
                                        rel_score,
                                        self.get_full_url(title_link['href']),
                                        country.strip()
                                        )
        return job_info

    def add_jobs(self, jobs_list: list):
        with requests.get(url, headers=headers) as response:
            if response.status_code == 200:
                html = response.content
                soup = BeautifulSoup(html, "html.parser")
                jobs = soup.find_all('div',
                                     class_='resultsRow phd-result-row-standard phd-result row py-2 w-100 px-0 m-0')
                for job in jobs:
                    jobs_list.append(self.parse_job(job))
                    print(jobs_list[-1])
        return jobs_list


if __name__ == "__main__":

    url = 'https://www.findaphd.com/phds/bioinformatics/?30M78yY0'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    weighted_kw = [('genetic', 3), ('biomedicine', 2), ('gene', 1)]
    csv_name = 'results.csv'

    jobs_list = []
    findaphd = FindAPhd(url, weighted_kw, headers)
    jobs_list = findaphd.add_jobs(jobs_list)

    with open(csv_name, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, jobs_list[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(jobs_list)
