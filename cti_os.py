import requests
import xml.etree.ElementTree as et
import sqlite3

################################################################################################################################################################################################
def call_CTI_OS_service(username, password, url):
    '''
    Sends a request in the XML form to CTI_OS service
    Keyword arguments: username, password and url address which will be used for CTI_OS request
    Returns: XML file with all POSIDENT attributes
    '''

    request = '''
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:v2="http://katastr.cuzk.cz/ctios/types/v2.8">
      <soapenv:Header> 
          <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"> 
            <wsse:UsernameToken wsu:Id="UsernameToken-3"> 
              <wsse:Username>{}</wsse:Username> 
              <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{}</wsse:Password> 
            </wsse:UsernameToken> 
          </wsse:Security> 
      </soapenv:Header> 
      <soapenv:Body> 
        <v2:CtiOsRequest> 
          <v2:pOSIdent>JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/+MIy6CahvfHgTVB/XVJb8QtDY/BLa1qLpU8MXWteZ3M=</v2:osIdent> 
        </v2:CtiOsRequest> 
      </soapenv:Body>
    </soapenv:Envelope>
    '''.format(username,password)

    headers = {'Content-Type':'text/xml;charset=UTF-8',
               'User-Agent':'ReadyAPI-MC',
               'Accept-Encoding': 'gzip,deflate',
               'SOAPAction': "http://katastr.cuzk.cz/ctios/ctios",
               #'Content-Length': '1187',
               #'Host': 'wsdptrial.cuzk.cz',
               'Connection': 'Keep-Alive'}

    CTI_OS_xml = requests.post(url, data = request, headers = headers).text
    return(CTI_OS_xml)

def parse_CTI_OS_xml(CTI_OS_xml):
    '''
    Parses XML returned by CTI_OS service into desired parts which will later represent database table atributes
    Keyword arguments: xml file to be parsed
    Returns: particular parts in a string format
    '''

    root = et.fromstring(CTI_OS_xml)
    #tree = et.ElementTree(root)

    pOSIdent = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent').text
    osId = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}osId').text
    stavDat = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}stavDat').text
    datumVzniku = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku').text
    priznakKontext = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}priznakKontext').text
    rizeniIdVzniku = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku').text
    partnerBsm1 = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm1').text
    partnerBsm2 = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm2').text
    opsubType = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}opsubType').text
    charOsType = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}charOsType').text
    nazev = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazev').text
    nazevU = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazevU').text
    datumVzniku2 = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku2').text
    rizeniIdVzniku2 = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku2').text

    return ( pOSIdent, osId, stavDat, datumVzniku, priznakKontext, rizeniIdVzniku, partnerBsm1, partnerBsm2, opsubType,
    charOsType, nazev, nazevU, datumVzniku2, rizeniIdVzniku2)

#################################################################################################################################################################################################

username = 'WSTEST'
password = 'WSHESLO'
url = 'https://wsdptrial.cuzk.cz/trial/ws/ctios/2.8/ctios'

CTI_OS_xml = call_CTI_OS_service(username, password, url) # CTI_OS request with upper parameters
print(CTI_OS_xml) #requested XML

(pOSIdent, osId, stavDat, datumVzniku, priznakKontext, rizeniIdVzniku, partnerBsm1, partnerBsm2, opsubType,
    charOsType, nazev, nazevU, datumVzniku2, rizeniIdVzniku2) = parse_CTI_OS_xml(CTI_OS_xml) #parsing function

# printing of parsed attributes (count = 12)
print("posident:{}".format(pOSIdent)) #superior
print("os_id:{}".format(osId)) #superior
print("stav:{}".format(stavDat))
print("datumVzniku:{}".format(datumVzniku))
print("priznakKontext:{}".format(priznakKontext))
print("rizeniIdVzniku:{}".format(rizeniIdVzniku))
print("partnerBsm1:{}".format(partnerBsm1))
print("partnerBsm2:{}".format(partnerBsm2))
print("opsubType:{}".format(opsubType))
print("charOsType:{}".format(charOsType))
print("nazev:{}".format(nazev))
print("nazevU:{}".format(nazevU))
print("datumVzniku2:{}".format(datumVzniku2))
print("rizeniIdVzniku2:{}".format(rizeniIdVzniku2))


