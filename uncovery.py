import os
import sys
import requests
from termcolor import cprint
from termcolor import colored
import json
import pwinput

def signin(email, password):
    cprint("Signin...","yellow")
    r = requests.post('https://api.uncovery.io/v1/auth/signin', data={'email': email,'password': password})
    response = r.json()
    cprint(response,'cyan')
    if r.ok:
        cprint(response['request']['message'],"green")
        return response['data']['accessToken']
    else:
        cprint(response['message'],"red")
        sys.exit(0)

def getAllEntities(token):
    cprint("Getting all Entities...","yellow")
    header = {'Authorization': 'Bearer ' + token}
    payload = {'pageSize':'100','sortBy':'name','orderBy':'asc'} 
    r = requests.get('https://api.uncovery.io/v1/entities', params=payload,headers=header)
    response = r.json()
    cprint(response,'cyan')
    
    if r.ok:
        cprint(response['request']['message'],"green")
        entitiesDict = {}
        for entity in response['data']:
            cprint("Entity : " + entity['name'],"yellow")
            cprint("ID : " + str(entity['id']),"cyan")
            cprint("Host(s) : " + str(entity['count']['host']),"cyan")
            cprint("Subdomain(s) : " + str(entity['count']['subdomain']),"cyan")
            entitiesDict[entity['name']] = str(entity['id'])
        return entitiesDict
    else:
        cprint(response['message'],"red")
        sys.exit(0)



if __name__ == '__main__':
    # check arguments
    email = password = ''
    if ((len(sys.argv) == 2) or (len(sys.argv) > 3)):
        cprint("Error, usage is: python {0} <email> <password>".format(sys.argv[0]),"red")
        cprint("Error, usage is: python {0} ".format(sys.argv[0]),"red")
        sys.exit(1)
    elif (len(sys.argv) == 3):
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = raw_input("Email: ")
        password = pwinput.pwinput(prompt='Password: ', mask='*')
    
    accessToken = signin(email,password)
    entitiesID = getAllEntities(accessToken)
    for entity, id in entitiesID.items():
        print(colored(entity, 'red') + colored(id, 'green'))
