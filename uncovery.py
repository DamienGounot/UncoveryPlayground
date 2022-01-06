import os
import sys
import requests
from requests.models import Response
from termcolor import cprint
from termcolor import colored
import colorama
import json
import pwinput
import numpy as np
from  openpyxl import Workbook

#https://api.uncovery.io/v1/documentation

def signin(email, password):
    cprint("Signin...","yellow")
    r = requests.post('https://api.uncovery.io/v1/auth/signin', data={'email': email,'password': password})
    response = r.json()
    #cprint(response,'cyan')
    if r.ok:
        cprint(response['request']['message'],"green")
        return response['data']['accessToken']
    else:
        cprint(response['message'],"red")
        sys.exit(0)

def createAndSendAuthRequest(token,url,payload):
    header = {'Authorization': 'Bearer ' + token}
    r = requests.get(url, params=payload,headers=header)
    response = r.json()
    #cprint(response,'cyan')
    return r,response
    
def getAllEntities(token,url,payload):
    cprint("Getting all Entities...","yellow")
    r,response = createAndSendAuthRequest(token,url,payload) 
    
    if r.ok:
        cprint(response['request']['message'],"green")
        entitiesDict = {}
        for entity in response['data']:
            print(colored(entity['name'], 'magenta') + colored(' : '+str(entity['id']),'yellow'))
            entitiesDict[entity['name']] = str(entity['id'])
        return entitiesDict
    else:
        cprint(response['message'],"red")
        sys.exit(0)

def getAllCartographyOfAnEntity(entitiesAndID,token): #useless for now, work in progress
    for entity, id in entitiesAndID.items():
        print(colored("Getting all Cartography of entity: ","yellow") + colored(entity, 'magenta') + colored(' ...','yellow'))
        url = "https://api.uncovery.io/v1/entities/"+ str(id) +"/cartographies"
        payload = "pageSize=20&page=1&sortBy=createdAt&orderBy=desc"
        r,response = createAndSendAuthRequest(token,url,payload)
        if r.ok:
            cprint(response['request']['message'],"green")
            while True:
                if str(response['pageInfo']['hasNextPage']) == 'False':
                    pass
                    break
                else:
                    pass
        else:
            cprint(response['message'],"red")

def getAllAssetsOfAnEntity(entitiesAndID,token,assetType):
    AssetsDict = {}
    for entity, id in entitiesAndID.items():
        pageNumber = 1
        ipsDict = {}    
        while True:
            print(colored("Getting all Assets of entity: ","yellow") + colored(entity, 'magenta') + colored(' Page : ','yellow') + colored(str(pageNumber),'cyan') + colored(' ...','cyan'))
            url = "https://api.uncovery.io/v1/entities/"+ str(id) +"/assets"
            payload = "type="+assetType+"&pageSize=20&page="+str(pageNumber)+"&sortBy=lastChanges&orderBy=desc"
            r,response = createAndSendAuthRequest(token,url,payload)
            if r.ok:
                cprint(response['request']['message'],"green")
           
                if str(response['pageInfo']['hasNextPage']) == 'False':
                    for item in response['data']:
                        ipsDict[item['id']] = item['value']
                    print(colored("No more page ","yellow") + colored(entity, 'magenta') + colored(' Page : ','yellow') + colored(str(pageNumber),'cyan') + colored(' !','yellow'))
                    break
                else:
                    for item in response['data']:
                        ipsDict[item['id']] = item['value']
                    pageNumber +=1
                    payload = "type="+(assetType)+"&pageSize=20&page="+str(pageNumber)+"&sortBy=lastChanges&orderBy=desc"
                    r,response = createAndSendAuthRequest(token,url,payload)
                    for item in response['data']:
                        ipsDict[item['id']] = item['value']
                    print(colored("Send request for page ","yellow") + colored(entity, 'magenta') + colored(' Page : ','yellow') + colored(str(pageNumber),'cyan'))
            else:
                cprint(response['message'],"red")
                break
        AssetsDict[id] = ipsDict

    # #For display only
    # for entity, id in entitiesAndID.items():
    #     print(colored("Display result for : ","yellow") + colored(entity, 'green') + colored(' is : ','yellow'))
    #     for idEntity, ipsDict in AssetsDict.items():
    #         if id == idEntity:
    #             for ipId, ipValue in ipsDict.items():
    #                 print(ipValue)
    
    return AssetsDict

def getOneAssetGraph(entitiesAndID,token,assetsAndEntitiesID):
    result = {}
    for entity, id in entitiesAndID.items():
        print(colored("For Entity : ","yellow") + colored(entity, 'magenta') + colored(' ...','yellow'))    
        entityDict = {}
        for idEntity, ipsDict in assetsAndEntitiesID.items():
            if id == idEntity:
                for ipId, ipValue in ipsDict.items():
                    portTcpArray = []
                    portUdpArray = []
                    portsDict = {}
                    print(colored("Getting Graph of asset: ","yellow") + colored(ipValue, 'cyan') + colored(' ...','yellow'))
                    url = "https://api.uncovery.io/v1/entities/"+ str(id) +"/assets/" + str(ipId) + "/graph"
                    payload = "direction=out"
                    r,response = createAndSendAuthRequest(token,url,payload)
                    if r.ok:
                        cprint(response['request']['message'],"green")

                        for item in response['data']['nodes']:
                            if item['type'] == 'porttcp':
                                portTcpArray.append(item['value'])
                            if item['type'] == 'portudp':
                                portUdpArray.append(item['value'])
                        portsDict['TCP'] = portTcpArray
                        portsDict['UDP'] = portUdpArray
                        entityDict[ipValue] = portsDict
                    else:
                        cprint(response['message'],"red")
                        break
        result[entity] = entityDict
    return result

def getDifferentsPorts(jsonFile):
    with open(jsonFile,'r') as f_in:
        data = json.load(f_in)
        result = {}
        for entity in data:
            portArray = []
            for ip in data[entity]:
                for tcp in data[entity][ip]['TCP']:
                    portArray.append(int(tcp))
                for udp in data[entity][ip]['UDP']:
                    portArray.append(int(udp))
            raw = np.array(portArray)
            uniquePorts = np.unique(raw)
            sortedAndUniquePorts = sorted(uniquePorts)
            result[entity] = sortedAndUniquePorts
    return result

def createExcelSheets(entitiesAndID,portList,jsonData): #WIP
    wb1 = Workbook()
    for entity,id in entitiesAndID.items():
        ws = wb1.create_sheet(entity)
    wb1.save('output.xlsx')

if __name__ == '__main__':
    colorama.init()
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
        email = input("Email: ")
        password = pwinput.pwinput(prompt='Password: ', mask='*')
    
    accessToken = signin(email,password)
    entitiesAndID = getAllEntities(accessToken,url = 'https://api.uncovery.io/v1/entities', payload = {'pageSize':'100','sortBy':'name','orderBy':'asc'})
    #getAllCartographyOfAnEntity(entitiesAndID,accessToken) #useless for now
    assetsAndEntitiesID = getAllAssetsOfAnEntity(entitiesAndID,accessToken,"ipv4")
    openedPortsByIPForEachEntity = getOneAssetGraph(entitiesAndID,accessToken,assetsAndEntitiesID)

    jsonData = json.dumps(openedPortsByIPForEachEntity, sort_keys=True)
    orig_stdout = sys.stdout
    sys.stdout = open('data.json', 'w+')
    print(jsonData)
    sys.stdout = orig_stdout
    portListForEachEntity = getDifferentsPorts('data.json')
    createExcelSheets(entitiesAndID,portListForEachEntity,jsonData)
