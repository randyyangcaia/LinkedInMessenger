from LinkedInMessenger import LinkedInMessenger
from pw import USERNAME, PASSWORD, DRIVER_PATH

if __name__ == '__main__':
    msg = LinkedInMessenger(USERNAME, PASSWORD, DRIVER_PATH, False)
    #msg = LinkedInMessenger(USERNAME, PASSWORD, DRIVER_PATH)
    msg.init_driver()
    msg.login()
    # msg.merge_table()
    msg.get_active_connection()
    #msg.retrieve_all_connection()
    # msg.send_message(r'https://www.linkedin.com/in/siyu-jiang-bb9a9bb9/')
    # msg.batch_message()
    # msg.delete_contact()
