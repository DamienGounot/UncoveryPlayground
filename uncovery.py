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
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
import traceback

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
                            tmpDict = {}
                            tmpDict['port'] = item['value']
                            tmpDict['detail'] = "FIXME"
                            if item['type'] == 'porttcp':
                                portTcpArray.append(tmpDict)
                            if item['type'] == 'portudp':
                                portUdpArray.append(tmpDict)
                        portsDict['TCP'] = portTcpArray
                        portsDict['UDP'] = portUdpArray
                        entityDict[ipValue] = portsDict
                    else:
                        cprint(response['message'],"red")
                        break
        result[entity] = entityDict
    return result

def getDifferentsPorts(jsonFile):
    result = {}
    cprint('Retrieve every used ports...','yellow')
    try:
        with open(jsonFile,'r') as f_in:
            data = json.load(f_in)
            for entity in data:
                print(colored('For entity ','yellow') + colored(entity, 'magenta') + colored(' :','yellow'))
                TCPportArray = []
                UDPportArray = []
                portsDict = {}   
                for ip in data[entity]:
        
                    for tcp in data[entity][ip]["TCP"]:
                        TCPportArray.append(int(tcp['port']))
                    for udp in data[entity][ip]["UDP"]:
                        UDPportArray.append(int(udp['port']))
                TCPraw = np.array(TCPportArray)
                UDPraw = np.array(UDPportArray)
                TCPuniquePorts = np.unique(TCPraw)
                UDPuniquePorts = np.unique(UDPraw)
                TCPsortedAndUniquePorts = sorted(TCPuniquePorts)
                UDPsortedAndUniquePorts = sorted(UDPuniquePorts)
                portsDict["TCP"] = TCPsortedAndUniquePorts
                portsDict["UDP"] = UDPsortedAndUniquePorts
                result[entity] = portsDict
                print(colored('TCP: ','magenta') + colored(TCPsortedAndUniquePorts,'cyan'))
                print(colored('UDP: ','magenta') + colored(UDPsortedAndUniquePorts,'cyan'))
        print(colored('Success retrieving ports','green'))
    except:
        print(colored('Error retrieving ports','red'))
    return result

def cleanSubdirectory(directory):
    print(colored("Removing files in \" ",'yellow') + colored(directory,'magenta') + colored(" \" directory...","yellow"))
    if os.path.exists(directory):
        for files in os.listdir(directory):
            os.remove(os.path.join(directory, files))
    else:
        try:
            os.mkdir(directory)
            print(colored('Cleaning success','green'))
        except Exception:
            print(colored("Error : could not create " + directory + " subdirectory !",'red'))

def createExcelSheets(entitiesAndID,portList,jsonFile): #WIP
    cleanSubdirectory('output')
    wb1 = Workbook()
    try:
        print(colored('Creating Excel output...','yellow'))
        for entity,id in entitiesAndID.items():
            actualPortIndex = actualIpIndex = 2
            ws = wb1.create_sheet(entity)
            with open(jsonFile,'r') as f_in:
                data = json.load(f_in)
                for ip in data[entity]:
                    ws.cell(row = actualIpIndex, column = 1).value = str(ip)
                    for protocol in portList[entity]:
                        for port in portList[entity][protocol]:
                            ws.cell(row = 1, column = actualPortIndex).value = protocol.lower()+'/'+str(port)
                            ws.cell(row = 1, column = actualPortIndex).alignment = Alignment(horizontal='center', textRotation = 90)
                            ws.column_dimensions[get_column_letter(actualPortIndex)].width = 3
                            #if (str(port) in data[entity][ip][protocol]): # A FIX, condition de detection
                            if any(x['port'] == str(port) for x in data[entity][ip][protocol]):    
                                ws.cell(row = actualIpIndex, column = actualPortIndex).value = 'X'
                                ws.cell(row = actualIpIndex, column = actualPortIndex).alignment = Alignment(horizontal='center')
                            actualPortIndex = actualPortIndex + 1
                    actualPortIndex = 2 # reset Index port
                    actualIpIndex = actualIpIndex + 1
            ws.row_dimensions[1].height = 50
            ws.freeze_panes = "A2"
            ws.column_dimensions['A'].width = 15
        wb1.save(os.path.join('output','output.xlsx'))
        print(colored('Success when creating Excel file','green'))
    except:
        print(colored('Error when creating Excel file','red'))
        traceback.print_exc()

def diff(obj1, obj2):
    change = []
    # vérifier si des ips ont ete ajoutees ou supprimes dans le scope
    del_ip = [ x for x in obj1 if not x in obj2 ]
    add_ip = [ x for x in obj2 if not x in obj1 ]
    for i in del_ip:
        change.append({'type':'removeip', 'ip':i})
    for i in add_ip:
        change.append({'type':'addip', 'ip':i})
    #  verifier les differences sur les ports
    interlist = obj1.keys() & obj2.keys()
    for protocol in ['TCP', 'UDP']:
        for i in interlist :
            ports1 = [ x.get('port') for x in obj1.get(i).get(protocol)]
            ports2 = [ x.get('port') for x in obj2.get(i).get(protocol)]
            add_ports = [ x for x in ports2 if not x in ports1]
            del_ports = [ x for x in ports1 if not x in ports2]

            for p in add_ports:
                change.append({'type':'addport', 'ip':i, 'port':p, 'protocol':protocol})
          
            for p in del_ports:
                change.append({'type':'delport', 'ip':i, 'port':p, 'protocol':protocol})

    
    return change

def getDiffBetweenEntity(entitiesAndID,previous,actual):
    previousData = actualData = None
    with open(previous,'r') as previousFile:
            previousData = json.load(previousFile)
    with open(actual,'r') as actualFile:
            actualData = json.load(actualFile)
    print(colored("======= ","yellow")+colored("Changes","red")+colored(" =======","yellow"))
    for entity, idEntity in entitiesAndID.items():
        print(colored("======= ","yellow")+colored(entity,"magenta")+colored(" =======","yellow"))
        print(diff(previousData[entity],actualData[entity]))
        #Edit Excel ici
        

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
    assetsAndEntitiesID = getAllAssetsOfAnEntity(entitiesAndID,accessToken,"ipv4")
    openedPortsByIPForEachEntity = getOneAssetGraph(entitiesAndID,accessToken,assetsAndEntitiesID)
    jsonData = json.dumps(openedPortsByIPForEachEntity, sort_keys=True)
    orig_stdout = sys.stdout
    sys.stdout = open('data.json', 'w+')
    print(jsonData) # Save every open tcp/udp ports
    sys.stdout = orig_stdout
    portListForEachEntity = getDifferentsPorts('data.json') # list of tcp/udp used ports
    #print(colored(portListForEachEntity,"cyan"))
    createExcelSheets(entitiesAndID,portListForEachEntity,'data.json')
        
    try:
        print(colored('Compute difference since last run...','yellow'))
        getDiffBetweenEntity(entitiesAndID,"previous.json","data.json")
        os.remove('previous.json')
    except:
        print(colored('Error when computing !','red'))
    os.rename('data.json', 'previous.json')
    print(colored('Finish !','green'))    
  
