import click
import json
import datetime
import requests
import sys
import pandas as pd


def getApiToken():
    with open('access.json') as json_file:
        data = json.load(json_file)
        return data['apitoken']


def getDomain():
    with open('access.json') as json_file:
        data = json.load(json_file)
        return data['domain']


def getHost():
    with open('access.json') as json_file:
        data = json.load(json_file)
        return data['host']


def startRun(run):
    response = requests.post(url=request_url + 'synchronizationRuns/' + run['id'] + '/start?test=false', headers=header)


def status(run):
    response = requests.get(url=request_url + 'synchronizationRuns/' + run['id'] + '/status', headers=header)
    return (response.json())


#Need extension when adding new sources
def createRun(data, source):
    time = str(datetime.datetime.now().strftime("%Y-%m-%d") + "T00:00:00.000Z")
    content = []
    if source == 'Archer':
        ldif = {
            "connectorType": "importData",
            "connectorId": "archerImport",
            "connectorVersion": "1.0.0",
            "lxVersion": "1.0.0",
            "description": "Imports Applications from Archer export",
            "processingDirection": "inbound",
            "processingMode": "partial",
            "customFields": {},
            "content": content
        }
        for obj in data.index:
            content.append({
                    "type": "Application",
                    "id": str(data['BOA ID'][obj]),
                    "data": {"name": data['BOA Name'][obj],
                             "owner": data['BOA Owner'][obj] if '@' in str(data['BOA Owner'][obj]) else creatUserId(data['BOA Owner'][obj]),
                             "organisation": mapData(source, 'Financial Business Unit', data['Financial Business Unit'][obj]) if mapData(source, 'Financial Business Unit', data['Financial Business Unit'][obj]) else '',
                             "function": mapData(source, 'Business Function', data['Business Function'][obj]) if mapData(source, 'Business Function', data['Business Function'][obj]) else '',
                             "manager": data['BU BOA Rep'][obj] if '@' in str(data['BU BOA Rep'][obj]) else creatUserId(data['BU BOA Rep'][obj]),
                             "description": data['BOA Description'][obj],
                             "status": data['BOA Current Status'][obj],
                             "type": mapData(source, 'BOA Type', data['BOA Type'][obj]) if mapData(source, 'BOA Type', data['BOA Type'][obj]) else ''}
                })
        print('The LDIF file of the current run: ' + str(ldif))
        response = requests.post(url=request_url + 'synchronizationRuns/', headers=header, data=json.dumps(ldif))
        return (response.json())
    else:
        raise ValueError('No configuration for the source system with name: ' + source + ' found.')


def createProcessorRun(source):
    try:
        with open(source + 'Processor.json') as json_file:
            processors = json.load(json_file)
        response = requests.put(url=request_url + 'configurations/', headers=header, data=json.dumps(processors))
        return response
    except:
        raise ValueError('No processor configuration for the source system with name: ' + source + ' found.')


def getFactSheetsOfType(type):
    query = """
    {
      allFactSheets(filter: {facetFilters: [{facetKey: "FactSheetTypes", keys: ["%s"]}]}) {
        totalCount
        edges {
          node {
            id
            name
            displayName
            type
          }
        }
      }
    }
    """%(type)
    response = callGraphQL(query)
    return response


def mapData(source, fieldName, value):
    with open('dataMapping.json') as json_file:
        mapping = json.load(json_file)
    targetValue = ""
    for src in mapping:
        if src['source'] == source:
            for map in src['mapping']:
                if map['field'] == fieldName:
                    for trans in map['values']:
                        if trans['from']['expr'] == value:
                            targetValue = queryValueOfType(map['type'], trans['to']['expr'])
    return targetValue


def queryValueOfType(type, value):
    data = getFactSheetsOfType(type)
    for node in data['data']['allFactSheets']['edges']:
        if str(node['node']['displayName']).strip() == value:
            valueOfType = node['node']['id']
            return valueOfType


def callGraphQL(query):
    data = {"query": query}
    json_data = json.dumps(data)
    response = requests.post(url='https://' + getHost() + '/services/pathfinder/v1/graphql', headers=header, data=json_data)
    response.raise_for_status()
    return response.json()


def creatUserId(name):
    postfix = "@" + getDomain()
    fullname = name.split(",")
    userId = str(fullname[1]).lower().strip() + "." + str(fullname[0]).lower().strip() + postfix
    return userId


#init
auth_url = 'https://' + getHost() + '/services/mtm/v1/oauth2/token'
request_url = 'https://' + getHost() + '/services/integration-api/v1/'
response = requests.post(auth_url, auth=('apitoken', getApiToken()), data={'grant_type': 'client_credentials'})
response.raise_for_status()
header = {'Authorization': 'Bearer ' + response.json()['access_token'], 'Content-Type': 'application/json'}

@click.command()
@click.argument('filename', required=1)
@click.option('--source', prompt='Enter the source system: ', default='Archer', help='Enter the source system of the file')
def main(filename, source):
    try:
        input = pd.read_excel(filename)
        data = pd.DataFrame(input)
        createProcessorRun(source)
        run = createRun(data, source)
        startRun(run)
        while (True):
           if (status(run)['status'] == 'FINISHED'):
               print("The run with the ID: " + run['id'] + " has been executed successfully!")
               break
    except:
        print("Unexpected error:", sys.exc_info()[0])


if __name__ == '__main__':
    main()