import time
import pandas
import logging
from   config                            import *
from   MsgTemplate                       import MsgTemplate
from   retrying                          import retry
from   selenium                          import webdriver
from   selenium.webdriver.common.by      import By
from   selenium.webdriver.support.ui     import WebDriverWait
from   selenium.webdriver.support        import expected_conditions as EC
from   selenium.webdriver.chrome.options import Options

class LinkedInMessenger(object):

    def __init__(self,
                 username,
                 password,
                 driverPath,
                 headless = True
                 ):

        self.username   = username
        self.password   = password
        self.driverPath = driverPath
        self.headless   = headless 

    def init_driver(self):
        """
        Initializes instance of webdriver
        """
        
        if self.headless:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu') 
            self.driver = webdriver.Chrome(executable_path=self.driverPath, chrome_options=options)
        else:
            self.driver = webdriver.Chrome(self.driverPath)
        
        self.driver.wait = WebDriverWait(self.driver, SCROLL_PAUSE_TIME)
        return self.driver

    def login(self):
        """
        Logs into LinkedIn.com
        """
        
        self.driver.get(LINKEDIN_LOGIN)
        try:
            user_field = WebDriverWait(self.driver, SCROLL_PAUSE_TIME).until(
                EC.presence_of_element_located((By.ID, 'username')))

            pw_field = WebDriverWait(self.driver, SCROLL_PAUSE_TIME).until(
                EC.presence_of_element_located((By.ID, 'password')))

            login_button = WebDriverWait(self.driver, SCROLL_PAUSE_TIME).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'login__form_action_container ')))

            user_field.send_keys(self.username)
            time.sleep(SCROLL_PAUSE_TIME)
            pw_field.send_keys(self.password)
            time.sleep(SCROLL_PAUSE_TIME)
            login_button.click()

            logging.warning("Login successfully.")

        except Exception as e:
            logging.warning(str(e))

    def _go_to_connection(self):
        """
        Go to LinkedIn Connection webpage
        """        

        self.driver.get(LINKEDIN_CONNECTION)
        time.sleep(SCROLL_PAUSE_TIME)

    def _go_to_message(self):
        """
        Go to LinkedIn Message webpage
        """

        connection_btn = self.driver.find_element_by_id('messaging-tab-icon')
        connection_btn.click()
        time.sleep(SCROLL_PAUSE_TIME)
    
    @retry(stop_max_attempt_number = 5, wait_fixed = 3000)
    def scroll_action(self, component):
        """
        Scroll down action
        """
        
        if component:
            return self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);var lenOfPage=arguments[0].scrollHeight;return lenOfPage;", component)
        else:
            return self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")    
        
    def scroll_to_bottom(self, component = None):
        """
        Scroll to the bottom of the webpage
        """

        counter, match = 1, False
        len_of_page = self.scroll_action(component)

        while (match == False):

            last_count = len_of_page
            time.sleep(SCROLL_PAUSE_TIME)
            len_of_page = self.scroll_action(component)

            logging.warning('Iteration {}'.format(counter))
            
            counter += 1
            match = last_count == len_of_page

        logging.warning('Scroll to the bottom.')

    def retrieve_all_connection(self, rerun = 'Yes'):
        """
        Retrieve all connection from LinkedIn Connection webpage
        """

        self._go_to_connection()

        ### Scroll to the bottom of connection page ###########
        self.scroll_to_bottom()
        logging.warning('Start getting all contacts.')

        ### Pull result from connection page  ################
        result = []

        pane = self.driver.find_element_by_css_selector(".mn-connections"
                                                        ".mb4.artdeco-card.ember-view")
        li_list = pane.find_elements_by_tag_name("li")

        for li in li_list:

            try:

                link = li.find_element_by_css_selector(".mn-connection-card__link"
                                                       " .ember-view").get_attribute("href")
                name = li.find_element_by_css_selector(".mn-connection-card__name"
                                                       ".t-16.t-black.t-bold").text
                occupation = li.find_element_by_css_selector(".mn-connection-card__occupation"
                                                             ".t-14.t-black--light.t-normal").text

                values = [name, occupation, tag]
                logging.warning(values)
                result.append(values)

            except Exception as e:
                logging.warning(str(e))
                pass

        contact = pandas.DataFrame.from_dict(result)
        contact.columns = ['Name', 'Title', 'URL']
        logging.warning('All contacts are retrieved.')

        if rerun == 'No':

            old_contact = pandas.read_csv(LOCAL_PATH + ALL_CONTACTS, header='infer')
            contact = contact.append(old_contact)
            contact.drop_duplicates(inplace=True)

        contact.to_csv(LOCAL_PATH + ALL_CONTACTS, index=False, encoding='utf_8_sig')

    def get_active_connection(self):
        """
        Retrieve connection with active contact
        """
        self._go_to_message()

        all_contacts = self.driver.find_element_by_css_selector(".msg-conversations-container__conversations-list"
                                                                ".list-style-none.ember-view")

        self.scroll_to_bottom(all_contacts)
        logging.warning('Start getting all contacts.')

        result = []
        li_list = all_contacts.find_elements_by_tag_name("li")

        for li in li_list:

            try:

                li.click()
                time.sleep(SCROLL_PAUSE_TIME)

                name = li.find_element_by_css_selector(".msg-conversation-listitem__participant-names"
                                                       ".msg-conversation-card__participant-names"
                                                       ".truncate.pr1.t-16.t-black.t-normal").text
                logging.warning('{} is retrieved'.format(name))
                try:
                    message_container = self.driver.find_element_by_css_selector(".msg-s-message-list-container.relative.display-flex.mbA.ember-view")
                    message_box = message_container.find_element_by_css_selector(".msg-s-message-list-content.full-height.list-style-none.full-width")
                except Exception as e:
                    
                    try:
                        message_container = self.driver.find_element_by_css_selector(".msg-s-message-list-container.relative.display-flex.mtA.ember-view")
                        message_box = message_container.find_element_by_css_selector(".msg-s-message-list-content.list-style-none.full-width")
                    except Exception as e:
                        # logging.warning(str(e))
                        pass

                #message_box.click()
                time.sleep(SCROLL_PAUSE_TIME)

                message_li = message_box.find_elements_by_css_selector(".msg-s-message-list__event.clearfix")

                count = 0
                for message in message_li:

                        try:
                            link = message.find_element_by_css_selector(".msg-s-event-listitem__link.ember-view")
                            tag = link.get_attribute("href")
                            
                            if tag != MY_LINKEDIN:

                                count += 1

                        except Exception as e:
                            logging.warning(str(e))

                print([name, count])
                result.append([name, count])

            except Exception as e:
                logging.warning(str(e))
                pass

        active_contact = pandas.DataFrame.from_dict(result)
        active_contact.columns = ['Name', 'Number_of_Message']
        logging.warning('All active contacts are complete.')

        active_contact.to_csv(LOCAL_PATH + 'active_contact.csv', index=False, encoding='utf_8_sig')
    
    def send_message(self, url, name):
        """
        Send message to target recipient
        """

        self.driver.get(url)
        time.sleep(SCROLL_PAUSE_TIME)

        try:
            message_button = self.driver.find_element_by_css_selector('.pv-s-profile-actions'
                                                                      '.pv-s-profile-actions--message'
                                                                      '.ml2.artdeco-button.artdeco-button--2'
                                                                      '.artdeco-button--primary.ember-view')

            message_button.click()

            time.sleep(SCROLL_PAUSE_TIME)

            input_box = self.driver.find_element_by_css_selector('.msg-form__contenteditable'
                                                                 '.t-14.t-black--light.'
                                                                 't-normal.flex-grow-1.notranslate')
            message = MsgTemplate.prepare_message(name)
            input_box.send_keys(message)

            time.sleep(SCROLL_PAUSE_TIME)

            send_button = self.driver.find_element_by_css_selector('.msg-form__send-button.artdeco-button'
                                                                   '.artdeco-button--1')
            send_button.click()

            logging.warning("Message is delivered to {0}.".format(name))

        except Exception as e:
            logging.warning(str(e))
            logging.warning("Fails to message {0}.".format(name))

    def batch_message(self):
        """
        Send messages to target recipients with fixed templates
        """

        email_recipients = pandas.read_csv(LOCAL_PATH + TARGET_CONTACTS, header='infer')

        for index, row in email_recipients.iterrows():

            self.send_message(row['URL'], row['Name'].split(' ')[0])
            time.sleep(SCROLL_PAUSE_TIME)
    
    def delete_contact(self):
        """
        Batch to delete connection. Use with caution.
        """

        contact = pandas.read_csv(LOCAL_PATH + DELETE_CONTACTS, header='infer')
        delete_contact = contact[contact['To_Delete'] == 'YES']

        for index, row in delete_contact.iterrows():

            self.driver.get(row['URL'])
            time.sleep(SCROLL_PAUSE_TIME)

            try:
                more_button = self.driver.find_element_by_css_selector('.pv-s-profile-actions__overflow-toggle'
                                                                    '.artdeco-button.artdeco-button--secondary'
                                                                    '.artdeco-button--3.artdeco-button--muted'
                                                                    '.mr2.mt2.artdeco-button.artdeco-button--muted'
                                                                    '.artdeco-button--2.artdeco-button--secondary'
                                                                    '.ember-view')
                more_button.click()

                time.sleep(SCROLL_PAUSE_TIME)

                delete_button = self.driver.find_element_by_css_selector('.pv-s-profile-actions.'
                                                                      'pv-s-profile-actions--disconnect.'
                                                                      'pv-s-profile-actions__overflow-button.'
                                                                      'full-width.text-align-left')

                delete_button.click()

                contact = contact[contact['Name'] != row['Name']]

                time.sleep(SCROLL_PAUSE_TIME)

                logging.warning("Delete {0}.".format(row['Name']))

            except Exception as e:
                logging.warning("Fails to delete {0}.".format(row['Name']))

            contact.to_csv(LOCAL_PATH + ALL_CONTACTS, index=False)

    @staticmethod
    def merge_table():

        old_contact = pandas.read_csv(LOCAL_PATH + ALL_CONTACTS, header='infer')
        old_contact= old_contact.set_index('Name')

        active_contact = pandas.read_csv(LOCAL_PATH + 'active_contact.csv', header='infer')
        active_contact = active_contact.set_index('Name')

        contact = old_contact.join(active_contact, on='Name')
        contact.to_csv(LOCAL_PATH + 'contact_all.csv', index=True)
