#!/usr/bin/python 
 
import sys 
import requests 
import getpass 
import configparser as ConfigParser 
import base64 
import xml.etree.ElementTree as ET 
from bs4 import BeautifulSoup 
from os.path import expanduser 
from urllib.parse import urlparse, urlunparse 
import re
import boto3


##########################################################################
# Variables 

region = 'eu-west-1' 
outputformat = 'json'

awsconfigfile = '.aws\\credentials'

sslverification = True 
 
# idpentryurl: The initial URL that starts the authentication process. 
idpentryurl = 'https://corp-sts-prod.vodafone.com/adfs/ls/idpinitiatedsignon?loginToRp=urn:amazon:webservices' 
 
# Get the federated credentials from the user
print("")
username = input("Vodafone Email: \n")
password = getpass.getpass("Password: \n")


session = requests.Session() 
# Programmatically get the SAML assertion
# Opens the initial IdP url and follows all of the HTTP302 redirects, and
# gets the resulting login page
formresponse = session.get(idpentryurl, verify=sslverification)
# Capture the idpauthformsubmiturl, which is the final url after all the 302s
idpauthformsubmiturl = formresponse.url

# Parse the response and extract all the necessary values
# in order to build a dictionary of all of the form values the IdP expects
formsoup = BeautifulSoup(formresponse.text, 'lxml') #.decode('utf8'))
payload = {}
					 
for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
    name = inputtag.get('name','')
    value = inputtag.get('value','')
    if "user" in name.lower():
        #Make an educated guess that this is correct field for username
        payload[name] = username
    elif "email" in name.lower():
        #Some IdPs also label the username field as 'email'
        payload[name] = username
    elif "pass" in name.lower():
        #Make an educated guess that this is correct field for password
        payload[name] = password
    else:
        #Populate the parameter with existing value (picks up hidden fields in the login form)
        payload[name] = value
					 

					 
# Some IdPs don't explicitly set a form action, but if one is set we should
# build the idpauthformsubmiturl by combining the scheme and hostname
# from the entry url with the form action target
# If the action tag doesn't exist, we just stick with the idpauthformsubmiturl above

for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
    action = inputtag.get('action')
    if action:
        parsedurl = urlparse(idpentryurl)
        idpauthformsubmiturl = parsedurl.scheme + "://" + parsedurl.netloc + action
        break
        			 
# Performs the submission of the login form with the above post data
response = session.post(
    idpauthformsubmiturl, data=payload, verify=sslverification)

soup = BeautifulSoup(response.text, 'lxml')

assertion = '' 
for inputtag in soup.find_all('input'): 
    if(inputtag.get('name') == 'SAMLResponse'):
        assertion = inputtag.get('value')

if not assertion:
    try:
        print("Unable to login user {0}".format(
            soup.find('input', attrs={'name': 'UserName', 'type': 'email'}).get('value')))
        sys.exit(1)
    except Exception as err:
        print("Error.\n{0}".format(err))
        sys.exit(1)
    

# Parse the returned assertion and extract the authorized roles 
awsroles = [] 
root = ET.fromstring(base64.b64decode(assertion))
 
for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'): 
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'): 
        for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
            awsroles.append(saml2attributevalue.text)
 
for awsrole in awsroles: 
    chunks = awsrole.split(',') 
    if'saml-provider' in chunks[0]:
        newawsrole = chunks[1] + ',' + chunks[0] 
        index = awsroles.index(awsrole) 
        awsroles.insert(index, newawsrole) 
        awsroles.remove(awsrole)

# If I have more than one role, ask the user which one they want, 
# otherwise just proceed 
if len(awsroles) > 1: 
    i = 0 
    print("Please choose the role you would like to assume:" )
    for awsrole in awsroles: 
        print ('[', i, ']: ', awsrole.split(',')[0] )
        i += 1 

    print ("Selection: ",) 
    selectedroleindex = input() 
 
    # Basic sanity check of input 
    if int(selectedroleindex) > (len(awsroles) - 1): 
        print ('You selected an invalid role index, please try again' )
        sys.exit(0) 
    role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    principal_arn = "arn:aws:iam::049892596108:saml-provider/ADFS" #awsroles[int(selectedroleindex)].split(',')[1]
 
else: 
    role_arn = awsroles[0].split(',')[0] 
    principal_arn = "arn:aws:iam::049892596108:saml-provider/ADFS" #awsroles[0].split(',')[1]

client = boto3.client('sts')
token = client.assume_role_with_saml(
    RoleArn=role_arn,
    PrincipalArn=principal_arn,
    SAMLAssertion=assertion
)

# Write the AWS STS token into the AWS credential file
home = expanduser("~")
filename = home + '\\' + awsconfigfile
# Read in the existing config file
config = ConfigParser.RawConfigParser()
config.read(filename)
 
# Put the credentials into a default profile
if not config.has_section('default'):
    config.add_section('default')
 
config.set('default', 'output', outputformat)
config.set('default', 'region', region)
config.set('default', 'aws_access_key_id', token["Credentials"]["AccessKeyId"])
config.set('default', 'aws_secret_access_key', token["Credentials"]["SecretAccessKey"])
config.set('default', 'aws_session_token', token["Credentials"]["SessionToken"])
 
# Write the updated config file
with open(filename, 'w+') as configfile:
   config.write(configfile)

# Give the user some basic info as to what has just happened
print('----------------------------------------------------------------')
print('Your new access key pair has been stored in the AWS configuration file {0} under the default profile.'.format(filename))
print('Note that it will expire at {0}.'.format(token["Credentials"]["Expiration"]))
print('After this time you may safely rerun this script to refresh your access key pair.')
print('----------------------------------------------------------------')
