from datetime import time

import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from posts.models import ScrapeJob


class ArchiveIsSpider(scrapy.Spider):
    name = 'archive_is_spider'

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'DOWNLOAD_DELAY': 0,
    }

    def __init__(self, *args, **kwargs):
        self.platform = '8chan'
        self.jobs = []
        jobs = kwargs.pop('jobs', [])
        if jobs:
            self.jobs = ScrapeJob.objects.filter(pk__in=jobs.split(','))
            self.jobs.update(in_progress=True)
            self.start_urls = [job.url for job in self.jobs]
        super(ArchiveIsSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for job in self.jobs:
            yield SeleniumRequest(
                url=job.url,
                callback=self.parse_result,
                cb_kwargs={
                    'job_id': job.id,
                }
            )

    def parse_result(self, response, **kwargs):
        try:
            job_id = kwargs.get('job_id')
            job = self.jobs.get(pk=job_id)
            driver = response.request.meta['driver']
            try:
                # Did we get a Captcha redirect?
                captcha = driver.find_element_by_css_selector('h2 span:nth-of-type(1)')
                if 'Please complete the security check' in captcha.text:
                    # Let's try something a lil shady...
                    print('Attempting to bypass Captcha...')
                    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
                    WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'recaptcha-checkbox-border'))).click()

                    time.sleep(15)

            except Exception as e:
                # No Captcha
                pass

            op = driver.find_element_by_css_selector('form > div:nth-of-type(1) > div:nth-of-type(2)')
            comments = driver.find_elements_by_css_selector('form > div > div:nth-of-type(n+3)')

            # OP
            yield {
                'platform': self.platform,
                'board': job.board,
                'thread_no': job.thread_id,
                'header': op.find_element_by_css_selector('div:nth-of-type(1)').get_attribute('innerHTML'),
                'body': op.find_element_by_css_selector('div:nth-of-type(2)').get_attribute('innerHTML'),
                'url': job.url
            }

            # Comments
            for comment in comments:
                yield {
                    'platform': self.platform,
                    'board': job.board,
                    'thread_no': job.thread_id,
                    'header': comment.find_element_by_css_selector('div:nth-of-type(1)').get_attribute('innerHTML'),
                    'body': comment.find_element_by_css_selector('div:nth-of-type(3)').get_attribute('innerHTML'),
                    'url': job.url
                }

        except Exception as e:
            print('Exception scraping {}/{}...'.format(job.board, job.thread_id))
            print(e)
            job.error_count += 1
            job.save()
            pass

        finally:
            job.in_progress = False
            job.save()
