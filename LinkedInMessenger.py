import time
import pandas
import logging
from   config                            import *
from   MsgTemplate                       import MsgTemplate
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

        self.driver.get(LINKEDIN_CONNECTION)
        time.sleep(SCROLL_PAUSE_TIME)

    def _go_to_message(self):

        connection_btn = self.driver.find_element_by_id('messaging-tab-icon')
        connection_btn.click()

        time.sleep(SCROLL_PAUSE_TIME)
    
    @staticmethod
    def scroll_to_bottom(driver, component = None):
        
        scroll_action = "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        counter = 1
        if component:
            len_of_page = driver.execute_script(scroll_action, component)
        else:
            len_of_page = driver.execute_script(scroll_action)
        match = False

        while (match == False):

            last_count = len_of_page
            time.sleep(SCROLL_PAUSE_TIME * 2)
            
            if component:
                len_of_page = driver.execute_script(scroll_action, component)
            else:
                len_of_page = driver.execute_script(scroll_action)
            
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
        LinkedInMessenger.scroll_to_bottom(self.driver)
        logging.warning('Start getting all contacts.')

        ### Pull result from connection page  ################
        result = []

        pane = self.driver.find_element_by_css_selector(".mn-connections.mb4.artdeco-card.ember-view")

        # start from your target element, here for example, "header"
        all_li = pane.find_elements_by_tag_name("li")

        try:
            for x in all_li:
                # all_children_by_xpath = x.find_elements_by_xpath(".//*")

                try:

                    link = x.find_element_by_css_selector(".mn-connection-card__link.ember-view")
                    tag = link.get_attribute("href")

                    name = x.find_element_by_css_selector(".mn-connection-card__name.t-16.t-black.t-bold").text

                    occupation = x.find_element_by_css_selector(".mn-connection-card__occupation.t-14.t-black--light"
                                                          ".t-normal").text

                    values = [name, occupation, tag]
                    logging.warning(values)

                    result.append(values)

                except Exception as e:
                    logging.warning(str(e))
                    pass

        except Exception as e:
            print(str(e))

        contact = pandas.DataFrame.from_dict(result)
        contact.columns = ['Name', 'Title', 'URL']
        logging.warning('All contacts are complete.')

        if rerun == 'No':

            old_contact = pandas.read_csv(LOCAL_PATH + ALL_CONTACTS, header='infer')
            contact = contact.append(old_contact)
            contact.drop_duplicates(inplace=True)

        contact.to_csv(LOCAL_PATH + ALL_CONTACTS, index=False)

    def _send_message(self, url, name):

        self.driver.get(url)
        time.sleep(SCROLL_PAUSE_TIME)

        try:
            msg_btn = self.driver.find_element_by_css_selector(".pv-s-profile-actions.pv-s-profile-actions--message."
                                                           "artdeco-button.artdeco-button--3.mr2.mt2")
            msg_btn.click()

            time.sleep(SCROLL_PAUSE_TIME)

            input_box = self.driver.find_element_by_css_selector(".msg-form__contenteditable.t-14.t-black--light."
                                                                 "t-normal.flex-grow-1")
            msg = MsgTemplate.prepare_message(name)
            input_box.send_keys(msg)

            time.sleep(SCROLL_PAUSE_TIME)

            send_btn = self.driver.find_element_by_css_selector(".msg-form__send-button.artdeco-button."
                                                                "artdeco-button--1")
            send_btn.click()

            logging.warning("Message is delivered to {0}.".format(name))

        except Exception as e:
            logging.warning("Fails to message {0}.".format(name))

    def batch_message(self):
        """
        Batch to send LinkedIn messenge to connection with predefined template.
        """

        contact = pandas.read_csv(LOCAL_PATH + TARGET_CONTACTS, header='infer')

        for index, row in contact.iterrows():

            self._send_message(row['URL'], row['Name'].split(' ')[0])
            time.sleep(SCROLL_PAUSE_TIME)

    def get_active_connection(self):

        self._go_to_message()

        all_contacts = self.driver.find_element_by_css_selector(".msg-conversations-container__conversations-list"
                                                                ".list-style-none.ember-view")

        #last_height = self.driver.execute_script('return arguments[0].scrollHeight', all_contacts)

        #while True:

        #    self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', all_contacts)
        #    time.sleep(SCROLL_PAUSE_TIME * 4)

        #    # Calculate new scroll height and compare with last scroll height
        #    new_height = self.driver.execute_script('return arguments[0].scrollHeight', all_contacts)
        #    if new_height == last_height:
        #        logging.warning('Reach the bottom of the page.')
        #        break
        #    last_height = new_height

        LinkedInMessenger.scroll_to_bottom(self.driver, all_contacts)
        logging.warning('Start getting all contacts.')

        result = []
        # start from your target element, here for example, "header"
        all_li = all_contacts.find_elements_by_tag_name("li")

        try:
            for x in all_li:

                try:

                    x.click()
                    time.sleep(SCROLL_PAUSE_TIME)

                    name = x.find_element_by_css_selector(".msg-conversation-listitem__participant-names"
                                                          ".msg-conversation-card__participant-names"
                                                          ".truncate.pr1.t-16.t-black--light.t-normal").text
                    print(name)
                    msg_box = self.driver.find_element_by_css_selector('.msg-s-message-list-container.relative'
                                                                       '.display-flex.mtA.ember-view')

                    msg_box.click()
                    time.sleep(SCROLL_PAUSE_TIME)

                    msg_li = msg_box.find_elements_by_tag_name("li")

                    count = 0
                    for one_msg in msg_li:

                            try:
                                link = one_msg.find_element_by_css_selector(".msg-s-event-listitem__link.ember-view")
                                tag = link.get_attribute("href")

                                if tag != MY_LINKEDIN:

                                    count += 1
                                    pass

                            except Exception as e:
                                pass

                    print([name, count])
                    result.append([name, count])

                except Exception as e:
                    # logging.warning(str(e))
                    pass

        except Exception as e:
            # print(str(e))
            pass

        active_contact = pandas.DataFrame.from_dict(result)
        active_contact.columns = ['Name', 'Number_of_Message']
        logging.warning('All active contacts are complete.')

        # old_contact = pandas.read_csv(LOCAL_PATH + ALL_CONTACTS, header='infer')
        # old_contact= old_contact.set_index('Name')
        #
        # contact = old_contact.join(active_contact.set_index('Name'), on='Name')
        active_contact.to_csv(LOCAL_PATH + 'test.csv', index=True)

        return 0

    def merge_table(self):

        old_contact = pandas.read_csv(LOCAL_PATH + ALL_CONTACTS, header='infer')
        old_contact= old_contact.set_index('Name')

        active_contact = pandas.read_csv(LOCAL_PATH + 'test.csv', header='infer')
        active_contact = active_contact.set_index('Name')

        contact = old_contact.join(active_contact, on='Name')
        contact.to_csv(LOCAL_PATH + 'test1.csv', index=True)

    def delete_contact(self):
        """
        Batch disconnect contacts. Not reversible. Use with cautiously.
        """
        
        contact = pandas.read_csv(LOCAL_PATH + DELETE_CONTACTS, header='infer')
        delete_contact = contact[contact['To_Delete'] == 'YES']

        for index, row in delete_contact.iterrows():

            self.driver.get(row['URL'])
            time.sleep(SCROLL_PAUSE_TIME)

            try:
                more_btn = self.driver.find_element_by_css_selector('.pv-s-profile-actions__overflow-toggle'
                                                                    '.artdeco-button.artdeco-button--secondary'
                                                                    '.artdeco-button--3.artdeco-button--muted'
                                                                    '.mr2.mt2.artdeco-button.artdeco-button--muted'
                                                                    '.artdeco-button--2.artdeco-button--secondary'
                                                                    '.ember-view')

                more_btn.click()

                time.sleep(SCROLL_PAUSE_TIME)

                delete_btn = self.driver.find_element_by_css_selector('.pv-s-profile-actions.'
                                                                      'pv-s-profile-actions--disconnect.'
                                                                      'pv-s-profile-actions__overflow-button.'
                                                                      'full-width.text-align-left')

                delete_btn.click()

                contact = contact[contact['Name'] != row['Name']]

                time.sleep(SCROLL_PAUSE_TIME)

                logging.warning("Delete {0}.".format(row['Name']))

            except Exception as e:
                logging.warning("Fails to delete {0}.".format(row['Name']))

            contact.to_csv(LOCAL_PATH + ALL_CONTACTS, index=False)
