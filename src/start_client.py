#GET
import json
import requests
import sys

from colorama import init
from colorama import Fore, Back, Style
init(autoreset=True)

SERVER_URL = "http://127.0.0.1:5000"

def get_uploader(movie, body, s, counter):
    '''Navigate to a single uploader with a movie name and get the uploader name'''
    
    movie_name = movie["name"]
    uploader = "John Smith"
    email = "Anon@Anon.com"
    
    uploaders_all_href = body["@controls"]["mwl:uploaders-all"]["href"]
    #print("\nuploaders all href: " + str(uploaders_all_href))
    resp1 = s.get(SERVER_URL + uploaders_all_href)
    body = resp1.json()
    #print("\nuploaders all href: " + str(uploaders_all_href))
    #print("\nuploaders body: " + str(body))
    uploader_list = body["items"]
    #print("\nuploader_list: " + str(uploader_list))
    for uploader_dict in uploader_list:
        uploader_name = uploader_dict["uploader_name"]
        uploader_email = uploader_dict["email"]
        single_uploader_href = uploader_dict["@controls"]["self"]["href"]
        #print("\nsingle: " + str(single_uploader_href))
        resp2 = s.get(SERVER_URL + single_uploader_href)
        body2 = resp2.json()
        #print("\nbody2: " + str(body2))
        
        uploader_movies = body2["items"]
        #print("\nuploader_movies: " + str(uploader_movies))
        
        for movie_dict in uploader_movies:
            if movie_dict["name"] == movie_name:
                uploader = uploader_name
                email = uploader_email
            else:
                continue
        
    print(Fore.CYAN + "\n" + str(counter) + ": " + str(movie["name"]) + " (" + movie["genre"] + ")" + " Uploader: " + str(uploader) + " (Email: " + email + ")")
        
    
def display_movie_collection(s, resp):
    '''Display all movies from the database'''
    
    print(Fore.YELLOW + "\n****************************")
    body = resp.json()
    #Get current location, which should be movie collection from entry point
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    #Get response from all movies resource:
    resp = s.get(SERVER_URL + current_href)
    body = resp.json()
    #print("\nbody: " + str(body))
    #Get all items currently in the db:
    movie_items = body["items"]
    #Print all items:
    #print("\nmovie_items: " + str(movie_items))
    
    counter = 1
    for movie in movie_items:
        get_uploader(movie, body, s, counter)
        counter += 1
    print(Fore.GREEN + "\n{} movie(s) found!".format(len(movie_items)))

def check_item_from_db(resp, s, name, function_index):
    '''Check if item exists in the database. 1 = add, 2 = delete, 3 = edit'''
    
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    resp1 = s.get(SERVER_URL + current_href)
    body2 = resp1.json()
    
    movie_items = body2["items"]
    for movie in movie_items:
        if movie["name"] == name:
            print(Fore.RED + "\nMovie already exists!")
            if(function_index == 1):
                add_movie(s,resp)    
            if(function_index == 2):
                edit_movie(s,resp)

def submit_data(s, ctrl, data):
    resp = s.request(
        ctrl["method"],
        SERVER_URL + ctrl["href"],
        data=json.dumps(data),
        headers = {"Content-type": "application/json"}
    )
    print(str(resp))
    return resp

def add_uploader(s, resp):    
    
    print( Fore.YELLOW + "\nType the uploader name or type 1 to go back. Leave empty if you want to proceed anonymously.")
    uploader = input(">")
    if uploader == "1":
        launch_option_zero(s, resp)

    if uploader == "":
        uploader = "John Smith"
        email = "anon@anon.com"
    else:
        print( Fore.YELLOW + "\nType the uploader email or type 1 to go back.")
        email = input(">")
        if email == "1":
            launch_option_zero(s, resp)
        if email == "":
            email = "anon@anon.com"
    
    #Submit new uploader to the database:
    body = resp.json()
    movies_all_href = body["@controls"]["mwl:movies-all"]["href"]
    resp4 = s.get(SERVER_URL + movies_all_href)
    body = resp4.json()
    print("\nbody uploaders: " + str(body))
    uploaders_all_href = body["@controls"]["mwl:uploaders-all"]["href"]
    print("\nuploaders all href: " + str(uploaders_all_href))
    resp5 = s.get(SERVER_URL + uploaders_all_href)
    body = resp5.json()
    print("\nbody uploaders: " + str(body))
    
    uploader_to_add = {}
    
    try:
        control = body["@controls"]["mwl:add-uploader"]
    except KeyError:
        resp6 = s.get(SERVER_URL + uploaders_all_href)
        body4 = resp6.json()
        control = body["@controls"]["mwl:add-uploader"]  
    
    print("\nuploader: " + str(uploader))
    uploader_to_add["uploader_name"] = uploader
    uploader_to_add["email"] = email
    
    resp6 = submit_data(s, control, uploader_to_add)
    print(Fore.GREEN + "\nUploader added: {} with email: {}".format(uploader, email))
    return uploader, email
    
def add_movie(s, resp):
    '''Function for adding movie to the database'''
    
    print(Fore.YELLOW + "\n****************************")
    display_movie_collection(s, resp)
    movie_to_add = {}
    print(Fore.YELLOW + "\nType the name of the movie or type 1 to go back.")
    name = input(">")
    if name == "1":
        launch_option_zero(s, resp)
    
    check_item_from_db(resp, s, name, 1)
    
    print( Fore.YELLOW + "\nType the genre of the movie or type 1 to go back.")
    genre = input(">")
    if genre == "1":
        launch_option_zero(s, resp)

    uploader_name, email = add_uploader(s, resp)    
  
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
    movie_to_add["genre"] = genre
    movie_to_add["uploader"] = uploader_name
    movie_to_add["email"] = email
    
    resp3 = submit_data(s, control, movie_to_add)
    print(Fore.GREEN + "\nMovie added: {} with genre: {}. Uploader: {} ({}).".format(name, genre, uploader_name, email))
    add_movie(s, resp)
    
def delete_movie(s, resp):
    '''Function for deleting movie from the database'''

    display_movie_collection(s, resp)
    print(Fore.YELLOW + "\nType the name of the movie you wish to delete or Type '1' to return back")
    name = input(">")
    if name == "1":
        launch_option_zero(s, resp)
    
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    resp1 = s.get(SERVER_URL + current_href)
    body = resp1.json()
    
    
    try:
        movie_items = body["items"]
        item_found = False
        for movie in movie_items:
            #print(str(movie))            
            if movie["name"] == name:
                item_found = True
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
                
                print(Fore.RED + "Movie deleted: {}".format(name))
                delete_movie(s, resp)
        if item_found == False:
            print(Fore.RED + "\n Invalid Input! Movie with that name not found!")
            delete_movie(s, resp)
            
    except KeyError:
        print(Fore.RED + "\nError in handling your request!")
        launch_option_zero(s, resp)

def edit_movie(s, resp):
    '''Function for editing movies from the database'''
    
    print(Fore.YELLOW + "\n****************************")
    display_movie_collection(s, resp)
    print(Fore.YELLOW + "\nType the name of the movie you wish to edit or type 1 to go back.")
    name = input(">")
    
    if name == "1":
        launch_option_zero(s, resp)
    
    #print("\nType the NEW name for the movie")
    #new_name = input(">")
    
    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]["href"]
    resp1 = s.get(SERVER_URL + current_href)
    body2 = resp1.json()
    
    #Get schema
    
    schema_req = body2["@controls"]["mwl:add-movie"]["schema"]["required"]
    
    movie_items = body2["items"]
    item_found = False
    info_dict = {}
    for movie in movie_items:
        if movie["name"] == name:
            current_href = movie["@controls"]["self"]["href"]
            resp2 = s.get(SERVER_URL + current_href)
            body3 = resp2.json()
            item_found = True
            genre = movie["genre"]
    if item_found == False:
        print("\n Invalid Input! Movie with that name not found!")
        edit_movie(s, resp)
    
    #Edit info:
    edit_info = {}
    for req in schema_req:    
        print(Fore.YELLOW + "Type the new {} for the {} ({}) or press 1 to go back".format(req, name, genre))
        variable = input(">")
        if variable == "1":
            edit_movie(s, resp)
        edit_info[req] = variable
    
    try:
        control = body3["@controls"]["edit"]
    except KeyError:
        resp3 = s.get(SERVER_URL + body3["@controls"]["self"]["href"])
        body4 = resp.json()
        ctrl = body4["@controls"]["edit"]
    
    resp3 = submit_data(s, control, edit_info)
    print(Fore.GREEN + "\nMovie edited: {} with new info: {}".format(name, str(edit_info)))
    edit_movie(s, resp)
        
def back_button(from_index, s, resp):
    print(Fore.YELLOW + "1. Back")
    option = input(">")
    if option == "1":
        launch_option_zero(s, resp)
    else:
        print(Fore.RED + "Invalid option")
        if from_index == 1:
            launch_option_show(s, resp)
        if from_index == 2:
            launch_option_edit(s, resp)

def launch_option_show(s, resp):
    '''UI function for seeing all wishlisted movies'''
    
    print(Fore.YELLOW + "\n****************************")
    print(Fore.YELLOW + "\nHere are all currently wishlisted movies.")
    display_movie_collection(s, resp)
    back_button(1, s, resp)

def display_uploaders(s, resp):
    '''Display all uploaders from the database'''
    
    print(Fore.YELLOW + "\n****************************")
    body = resp.json()
    
    #print("\nbody entry: " + str(body))
    #Get current location, which should be movie collection from entry point
    movies_all_href = body["@controls"]["mwl:movies-all"]["href"]
    
    #Get movie collection location
    resp1 = s.get(SERVER_URL + movies_all_href)
    body = resp1.json()
    print("\nbody collection: " + str(body))
    
    #Get uploader collection location
    
    uploaders_all_href = body["@controls"]["mwl:uploaders-all"]["href"]
    print("\nbody href: " + str(uploaders_all_href))
    resp2 = s.get(SERVER_URL + uploaders_all_href)
    body = resp2.json()
    print("\nbody uploaders: " + str(body))
    
    #Get all items currently in the db:
    uploader_items = body["items"]
    #Print all items:
    
    counter = 1
    previous_name = ""
    for uploader in uploader_items:
        if previous_name == "John Smith":
            continue
        else:
            print(Fore.CYAN + "\n" + str(counter) + ": " + str(uploader["uploader_name"]) + " (" + uploader["email"] + ")")
            previous_name = uploader["uploader_name"]
            counter += 1
    print(Fore.GREEN + "\n{} uploader(s) found!".format(str(counter - 1)))
    
def launch_option_show_uploaders(s, resp):
    '''UI function for seeing all uploaders'''
    
    print(Fore.YELLOW + "\n****************************")
    print(Fore.YELLOW + "\nHere are all uploaders.")
    display_uploaders(s, resp)
    back_button(1, s, resp)

def launch_option_edit(s, resp):
    '''UI function for movie edit options'''
    
    print(Fore.YELLOW + "\n****************************")
    print(Fore.YELLOW + "\nAdd/Delete/Edit movies.")
    
    print(Fore.YELLOW + "\n 1. Add a new movie.")
    print(Fore.YELLOW + "\n 2. Delete existing movies.")
    print(Fore.YELLOW + "\n 3. Edit existing movies.")
    print(Fore.YELLOW + "\n 4. Back.")
    
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
            print(Fore.RED + "Invalid option")
            launch_option_edit(s, resp)

def launch_option_exit():
    '''Function for exit'''
    input("Bye bye!")
    sys.exit()

def launch_option_zero(s, resp):
    '''UI function for lobby'''

    body = resp.json()
    current_href = body["@controls"]["mwl:movies-all"]
    user_interface_on = True
    
    '''Print UI'''
    print(Fore.YELLOW + "\n****************************")
    print(Fore.YELLOW + "\nWelcome to Movie Wishlister!")
    print(Fore.YELLOW + "\n 1. See all wishlisted Movies.")
    print(Fore.YELLOW + "\n 2. See all uploaders.")
    print(Fore.YELLOW + "\n 3. Add/delete/edit movies.")
    print(Fore.YELLOW + "\n 4. Exit.")
    
    while(user_interface_on):
        
        option = input(">")
        try:
            int(option)
            if option != "1" and option != "2" and option != "3" and option != "4":
                print(Fore.RED + "\nInvalid option! Choose 1, 2, 3, 4!")
            
            if option == "1":
                launch_option_show(s, resp)
            elif option == "2":
                launch_option_show_uploaders(s, resp)
            elif option == "3":
                launch_option_edit(s, resp)
            else:
                launch_option_exit()
            
        except ValueError:
            print(Fore.RED + "\nInvalid option!")
                    
def launch_user_interface():
    
    print(Fore.YELLOW + "Connecting to the api...")


    #requests.get(SERVER_URL + "/api/artists/")
    #body = resp.json()

    with requests.Session() as s:
        s.headers.update({"Accept": "application/vnd.mason+json"})
        resp = s.get(SERVER_URL + "/api/")
        if resp.status_code != 200:
            
            print(Fore.RED + "\nUnable to access API.")
            print(Fore.RED + "Response: " + str(resp))
            
        else:
            print(Fore.GREEN + "\nConnected to the API!")
            launch_option_zero(s, resp)
            
if __name__ == "__main__":
    launch_user_interface()