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

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return None

def update_Export_vse_db(db_file, pOSIdent, stavDat, datumVzniku, priznakKontext, rizeniIdVzniku, partnerBsm1, partnerBsm2, opsubType, charOsType, nazev, nazevU, datumVzniku2, rizeniIdVzniku2):
    '''
    Updates attributes for particular posident into one SQLITE3 table row
    Keyword arguments: row attributes in a string format
    Returns: failed! if problem appears otherwise None
    '''

    conn = create_connection(db_file)
    conn.isolation_level = None

    try:
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION")
        cur.execute(''' UPDATE OPSUB SET stav_dat = ? WHERE id = ?''',(stavDat, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET datum_vzniku = ? WHERE id = ?''',(datumVzniku, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET priznak_kontextu = ? WHERE id = ?''',(priznakKontext, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET rizeni_id_vzniku = ? WHERE id = ?''',(rizeniIdVzniku, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET ID_JE_1_PARTNER_BSM = ? WHERE id = ?''',(partnerBsm1, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET ID_JE_2_PARTNER_BSM = ? WHERE id = ?''',(partnerBsm2, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET OPSUB_TYPE = ? WHERE id = ?''',(opsubType, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET CHAROS_KOD = ? WHERE id = ?''',(charOsType, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET NAZEV = ? WHERE id = ?''',(nazev, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET NAZEV_U = ? WHERE id = ?''',(nazevU, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET DATUM_VZNIKU2 = ? WHERE id = ?''',(datumVzniku2, pOSIdent))
        cur.execute(''' UPDATE OPSUB SET RIZENI_ID_VZNIKU2 = ? WHERE id = ?''',(rizeniIdVzniku2, pOSIdent))
        cur.execute("COMMIT TRANSACTION")
        cur.close()
        conn.close()

    except conn.Error:
        print("failed!")
        cur.execute("ROLLBACK TRANSACTION")
        cur.close()
        conn.close()
    return None

#################################################################################################################################################################################################

username = 'WSTEST'
password = 'WSHESLO'
url = 'https://wsdptrial.cuzk.cz/trial/ws/ctios/2.8/ctios' # access point to CTI_OS service
db = 'd:/pluginy_QGIS/Export_vse.db' # database -- necessary to change the source file

CTI_OS_xml = call_CTI_OS_service(username, password, url) # CTI_OS request with upper parameters
print(CTI_OS_xml) # requested XML

# parsing of requested XML
(pOSIdent, osId, stavDat, datumVzniku, priznakKontext, rizeniIdVzniku, partnerBsm1, partnerBsm2, opsubType, charOsType, nazev, nazevU, datumVzniku2, rizeniIdVzniku2) = parse_CTI_OS_xml(CTI_OS_xml)

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

# updating one row in the database by parsed attributes
update_Export_vse_db(db, pOSIdent, stavDat, datumVzniku, priznakKontext, rizeniIdVzniku, partnerBsm1, partnerBsm2, opsubType, charOsType, nazev, nazevU, datumVzniku2, rizeniIdVzniku2)

conn = create_connection(db)
cur = conn.cursor()
cur.execute("SELECT * FROM OPSUB where RIZENI_ID_VZNIKU2 is not null and RIZENI_ID_VZNIKU is not null")
updated_row = cur.fetchone()
print(updated_row) # controlling of the updated row