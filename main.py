from LinkedInMessenger import LinkedInMessenger
from pw import USERNAME, PASSWORD, DRIVER_PATH

if __name__ == '__main__':
    #msg = LinkedInMessenger(USERNAME, PASSWORD, DRIVER_PATH, False)
    msg = LinkedInMessenger(USERNAME, PASSWORD, DRIVER_PATH)
    msg.init_driver()
    msg.login()
    #LinkedInMessenger.merge_table()
    #msg.retrieve_all_connection()
    #msg.get_active_connection()
    msg.batch_message()
    #msg.delete_contact()
