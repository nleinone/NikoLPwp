#GET
import json
import requests
import sys

SERVER_URL = "http://127.0.0.1:5000"

def display_movie_collection(s, resp):
    '''Display all movies from the database'''
    
    body = resp.json()
    #Get current location, which should be movie collection from entry point
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    #Get response from all movies resource:
    resp = s.get(SERVER_URL + current_href)
    body = resp.json()
    #Get all items currently in the db:
    movie_items = body["items"]
    #Print all items:
    
    counter = 1
    for movie in movie_items:
        print("\n" + str(counter) + ": " + str(movie["name"]) + " (" + movie["genre"] + ")")

    print("\n{} movie(s) found!".format(len(movie_items)))

def submit_data(s, ctrl, data):
    resp = s.request(
        ctrl["method"],
        SERVER_URL + ctrl["href"],
        data=json.dumps(data),
        headers = {"Content-type": "application/json"}
    )
    print(str(resp))
    return resp

def add_movie(s, resp):

    movie_to_add = {}
    print("\nType the name of the movie or type 1 to go back.")
    name = input(">")
    if name == "1":
        launch_option_zero(s, resp)
        
    print("\nType the genre of the movie or type 1 to go back.")
    genre = input(">")
    if genre == "1":
        launch_option_zero(s, resp)
    #print("\nType the release year of the movie.")
    #release_year = input(">")
    
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    resp1 = s.get(SERVER_URL + current_href)
    body = resp1.json()
    
    #Submit new movie to the database:
    try:
        control = body["@controls"]["mwl:add-movie"]
    except KeyError:
        resp2 = s.get(SERVER_URL + current_href)
        body = resp2.json()
        control = body["@controls"]["mwl:add-movie"]  
    
    movie_to_add["name"] = name
    movie_to_add["genre"] = name
    #movie_to_add["year"] = name
    
    resp3 = submit_data(s, control, movie_to_add)
    print("\nMovie added: {} with genre: {}".format(name, genre))
    add_movie(s, resp)
    
def delete_movie(s, resp):
    
    display_movie_collection(s, resp)
    print("\nType the name of the movie you wish to delete or Type '1' to return back")
    name = input(">")
    if name == "1":
        launch_option_zero(s, resp)
    
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    resp1 = s.get(SERVER_URL + current_href)
    body = resp1.json()
    
    
    try:
        movie_items = body["items"]
        for movie in movie_items:
            #print(str(movie))
            
            if movie["name"] == name:
                #Move to individual movie with the delete control
                current_href = movie["@controls"]["self"]["href"]
                resp2 = s.get(SERVER_URL + current_href)
                body = resp2.json()
                #print(body)
                 
                try:
                    control = body["@controls"]["mwl:delete"]
                except KeyError:
                    resp3 = s.get(SERVER_URL + current_href)
                    body = resp3.json()
                    control = body["@controls"]["mwl:delete"]  
                movie_to_del = {}
                movie_to_del["name"] = name
                
                resp4 = submit_data(s, control, movie_to_del)
                
                print("Movie deleted: {}".format(name))
                delete_movie(s, resp)
                
    except KeyError:
        print("\nError in handling your request!")
        launch_option_zero(s, resp)

def edit_movie():

    display_movie_collection(s, resp)
    print("\nType the name of the movie you wish to edit")
    name = input(">")
    

def back_button(from_index, s, resp):
    print("1. Back")
    option = input(">")
    if option == "1":
        launch_option_zero(s, resp)
    else:
        print("Invalid option")
        if from_index == 1:
            launch_option_show(s, resp)
        if from_index == 2:
            launch_option_edit(s, resp)

    
def launch_option_show(s, resp):
    '''UI function for seeing all wishlisted movies'''
    
    print("\n****************************")
    print("\nHere are all currently wishlisted movies.")
    display_movie_collection(s, resp)
    back_button(1, s, resp)
    
    
def launch_option_edit(s, resp):
    '''UI function for movie edit options'''
    
    print("\n****************************")
    print("\nAdd/Delete/Edit movies.")
    
    print("\n 1. Add a new movie.")
    print("\n 2. Delete existing movies.")
    print("\n 3. Edit existing movies.")
    print("\n 4. Back.")
    
    option = input(">")
    
    if option == "1":
        add_movie(s, resp)
    elif option == "2":
        delete_movie(s, resp)
    elif option == "3":
        edit_movie(s, resp)
    else:
        if option == "4":
            launch_option_zero(s, resp)
        else:
            print("Invalid option")
            launch_option_edit(s, resp)
def launch_option_exit():
    '''Function for exit'''
    input("Bye bye!")
    sys.exit()

def launch_option_zero(s, resp):
    '''UI function for lobby'''

    #print(str(resp))
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]
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
                launch_option_show(s, resp)
            elif option == "2":
                launch_option_edit(s, resp)
            else:
                launch_option_exit()
            
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
            launch_option_zero(s, resp)
            
if __name__ == "__main__":
    launch_user_interface()