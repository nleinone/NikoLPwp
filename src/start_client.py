#GET
import json
import requests
import sys

def back_button(from_index):
    print("1. Back")
    option = input(">")
    if option == "1":
        launch_option_zero()
    else:
        print("Invalid option")
        if from_index == 1:
            launch_option_one()
        if from_index == 2:
            launch_option_two()

def display_movie_collection():
    print("Movie list")

def launch_option_one():
    '''UI function for seeing all wishlisted movies'''
    
    print("\n****************************")
    print("\nHere are all currently wishlisted movies.")
    display_movie_collection()
    back_button(1)
    
    
def launch_option_two():
    '''UI function for movie edit options'''
    
    print("\n****************************")
    print("\nAdd/Delete/Edit movies.")
    back_button(2)
    
def launch_option_three():
    '''Function for exit'''
    input("Bye bye!")
    sys.exit()

def launch_option_zero():
    '''UI function for lobby'''
    
    #print(str(resp))
    #body = resp.json()
    #current_href = body["@controls"]["maze:entrance"]["href"]
    #e_resp = s.get(SERVER_URL + current_href)
    #entry_body = e_resp.json()   
    user_interface_on = True
    
    '''Print UI'''
    print("\n****************************")
    print("\nWelcome to Movie Wishlister!")
    print("\n 1. See all wishlisted Movies.")
    print("\n 2. Add/delete/edit movies.")
    print("\n 3. Exit.")
    
    #switch = "east"
    #room_count = 0
    #visited_rooms = []
    while(user_interface_on):
        
        option = input(">")
        try:
            int(option)
            if option != "1" and option != "2" and option != "3":
                print("\nInvalid option! Choose 1, 2, or 3!")
            
            if option == "1":
                launch_option_one()
            elif option == "2":
                launch_option_two()
            else:
                launch_option_three()
            
        except ValueError:
            print("\nInvalid option!")
        
        #print(current_href)
        #room_count += 1
        #Get hrefs of neighbouring rooms:
        #if switch == "east":
        #try:
            #resp = s.get(SERVER_URL + current_href)
            #body = resp.json()
            
            #current_handle = body["handle"]
            #current_content = body["content"]
            #current_href = body["@controls"]["maze:east"]["href"]
            #not_found = check_win(current_content)
            
        #except Exception as e:
        #    print("Error occured: " + str(e))
                    
def launch_user_interface():
    
    print("Connecting to the api...")
    SERVER_URL = "http://127.0.0.1:5000"

    #requests.get(SERVER_URL + "/api/artists/")
    #body = resp.json()

    with requests.Session() as s:
        s.headers.update({"Accept": "application/vnd.mason+json"})
        resp = s.get(SERVER_URL + "/api/")
        if resp.status_code != 200:
            
            print("\nUnable to access API.")
            print("Response: " + str(resp))
            
        else:
            print("\nConnected to the API!")
            launch_option_zero()
            
if __name__ == "__main__":
    launch_user_interface()