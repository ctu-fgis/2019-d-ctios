###############################################################################
# Name:         CTI_OS
# Purpose:      Sends a request to CTI_OS service based on given posident array
#               and stores response to SQLITE DB
# Date:         May 2019
# Copyright:    (C) 2019 Linda Kladivova
# Email:        l.kladivova@seznam.cz
###############################################################################
#! python3

import requests
import xml.etree.ElementTree as et
import sqlite3
from sqlite3 import Error
import math
import os
import logging
from datetime import datetime


def remove_duplicates(array):
    """
    Remove duplicates in array
    Keyword arguments: array
    Returns: array with no duplicates
    """
    return list(dict.fromkeys(array))


def draw_up_xml_request(username, password, posident_array):
    """
    Put together a request in the XML form to CTI_OS service
    Keyword arguments: username, password and array of POSIDENTS
    Returns: XML file with all POSIDENT attributes
    """
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
        </v2:CtiOsRequest> 
      </soapenv:Body>
    </soapenv:Envelope>
    '''.format(username, password)

    j = 0
    for i in posident_array:
        root = et.fromstring(request)
        body = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}CtiOsRequest')
        id_tag = et.Element('{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent')
        id_tag.text = i
        body.insert(1, id_tag)
        request = et.tostring(root, encoding="unicode")
        j = j+1
    return request


def call_service(request, endpoint):
    """
    Sends a request in the XML form to CTI_OS service
    Keyword arguments: request and url address which will be used for CTI_OS request
    Returns: XML file with all POSIDENT attributes
    """
    headers = {'Content-Type': 'text/xml;charset=UTF-8',
               'Accept-Encoding': 'gzip,deflate',
               'SOAPAction': "http://katastr.cuzk.cz/ctios/ctios",
               'Connection': 'Keep-Alive'}

    response = requests.post(endpoint, data=request, headers=headers).text
    return response


def create_connection(db_file):
    """
    Create a database connection to the SQLite database specified by the db_file
    Keyword arguments:  database file
    Returns: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return None


def create_log_file(log_path):
    """ Create log file
    Keyword arguments: log_path
    Returns: Connection object or None
    """
    log_filename = datetime.now().strftime('logfile_%H_%M_%S_%d_%m_%Y.log')
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename= log_path + '/' + log_filename,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    return logging


def save_attributes_to_db(response, db_file, state_vector, logging):
    """
    1. Parses XML returned by CTI_OS service into desired parts which will represent database table attributes
    2. Connects to Export_vse.db
    3. Alters table by adding OS_ID column if not exists
    4. Updates attributes for all posidents in SQLITE3 table rows
    Keyword arguments: xml file returned by CTI_OS service, path to the database file and state information vector, logging
    Returns: failed! if problem appears otherwise updated state vector
    """

    root = et.fromstring(response)

    conn = create_connection(db_file)
    conn.isolation_level = None

    # for all tags within tag 'os' do this: parse and save attributes into OPSUB table
    for os in root.findall('.//{http://katastr.cuzk.cz/ctios/types/v2.8}os'):

        # Parse XML returned by CTI_OS service into desired parts

        # check errors of given posidents, if error occurs continue back to the function beginning
        if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}chybaPOSIdent') is not None:
            posident = os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent').text

            if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}chybaPOSIdent').text == "NEPLATNY_IDENTIFIKATOR":
                state_vector[0] = state_vector[0] + 1
                logging.error('POSIDENT {} NEPLATNY IDENTIFIKATOR'.format(posident))
                continue
            if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}chybaPOSIdent').text == "EXPIROVANY_IDENTIFIKATOR":
                state_vector[1] = state_vector[1] + 1
                logging.error('POSIDENT {}: EXPIROVANY IDENTIFIKATOR'.format(posident))
                continue
            if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}chybaPOSIdent').text == "OPRAVNENY_SUBJEKT_NEEXISTUJE":
                state_vector[2] = state_vector[2] + 1
                logging.error('POSIDENT {}: OPRAVNENY SUBJEKT NEEXISTUJE'.format(posident))
                continue

        # process next if no errors occur
        number_of_attributes = 38  # stiff constant value - does not change during the process
        list_of_attributes = [None] * number_of_attributes
        state_vector[3] = state_vector[3] + 1

        # poSIdent
        if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent') is not None:
            list_of_attributes[0] = os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent').text
        # stavDat
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}stavDat') is not None:
            list_of_attributes[1] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}stavDat').text
        # datumVzniku
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku') is not None:
            list_of_attributes[2] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku').text
        # datumZaniku
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumZaniku') is not None:
            list_of_attributes[3] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumZaniku').text
        # priznakKontext
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}priznakKontext') is not None:
            list_of_attributes[4] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}priznakKontext').text
        # rizeniIdVzniku
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku') is not None:
            list_of_attributes[5] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku').text
        # rizeniIdZaniku
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdZaniku') is not None:
            list_of_attributes[6] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdZaniku').text
        # partnerBsm1
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm1') is not None:
            list_of_attributes[7] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm1').text
        # partnerBsm2
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm2') is not None:
            list_of_attributes[8] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}partnerBsm2').text
        # idZdroj
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}idZdroj') is not None:
            list_of_attributes[9] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}idZdroj').text
        # opsubType
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}opsubType') is not None:
            list_of_attributes[10] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}opsubType').text
        #  charOsType
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}charOsType') is not None:
            list_of_attributes[11] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}charOsType').text
        #  ico
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}ico') is not None:
            list_of_attributes[12] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}ico').text
        #  doplnekIco
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}doplnekIco') is not None:
            list_of_attributes[13] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}doplnekIco').text
        #  nazev
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazev') is not None:
            list_of_attributes[14] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazev').text
        #  nazevU
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazevU') is not None:
            list_of_attributes[15] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazevU').text
        #  rodneCislo
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rodneCislo') is not None:
            list_of_attributes[16] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rodneCislo').text
        #  titulPredJmenem
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}titulPredJmenem') is not None:
            list_of_attributes[17] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}titulPredJmenem').text
        #  jmeno
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}jmeno') is not None:
            list_of_attributes[18] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}jmeno').text
        #  jmenoU
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}jmenoU') is not None:
            list_of_attributes[19] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}jmenoU').text
        #  prijmeni
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}prijmeni') is not None:
            list_of_attributes[20] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}prijmeni').text
        #  prijmeniU
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}prijmeniU') is not None:
            list_of_attributes[21] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}prijmeniU').text
        #  titulZaJmenem
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}titulZaJmenem') is not None:
            list_of_attributes[22] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}titulZaJmenem').text
        #  cisloDomovni
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cisloDomovni') is not None:
            list_of_attributes[23] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cisloDomovni').text
        #  cisloOrientacni
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cisloOrientacni') is not None:
            list_of_attributes[24] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cisloOrientacni').text
        #  nazevUlice
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazevUlice') is not None:
            list_of_attributes[25] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}nazevUlice').text
        #  castObce
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}castObce') is not None:
            list_of_attributes[26] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}castObce').text
        #  obec
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}obec') is not None:
            list_of_attributes[27] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}obec').text
        #  okres
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}okres') is not None:
            list_of_attributes[28] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}okres').text
        #  stat
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}stat') is not None:
            list_of_attributes[29] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}stat').text
        #  psc
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}psc') is not None:
            list_of_attributes[30] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}psc').text
        #  mestskaCast
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}mestskaCast') is not None:
            list_of_attributes[31] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}mestskaCast').text
        #  cpCe
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cpCe') is not None:
            list_of_attributes[32] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}cpCe').text
        #  datumVzniku2
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku2') is not None:
            list_of_attributes[33] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}datumVzniku2').text
        #  rizeniIdVzniku2
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku2') is not None:
            list_of_attributes[34] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}rizeniIdVzniku2').text
        #  kodAdresnihoMista
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}kodAdresnihoMista') is not None:
            list_of_attributes[35] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}kodAdresnihoMista').text
        #  idNadrizenePravnickeOsoby
        if os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}idNadrizenePravnickeOsoby') is not None:
            list_of_attributes[36] = os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}idNadrizenePravnickeOsoby').text
        #  osId
        if os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}osId') is not None:
            list_of_attributes[37] = os.find('{http://katastr.cuzk.cz/ctios/types/v2.8}osId').text

        print(list_of_attributes)

        #  Update table OPSUB
        try:
            cur = conn.cursor()
            cur.execute("BEGIN TRANSACTION")
            columns = [i[1] for i in cur.execute('PRAGMA table_info(OPSUB)')]
            if 'OS_ID' not in columns:
                cur.execute('ALTER TABLE OPSUB ADD COLUMN OS_ID TEXT')  # alters table by adding os_id column
            cur.execute(''' UPDATE OPSUB SET stav_dat = ? WHERE id = ?''', (list_of_attributes[1], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET datum_vzniku = ? WHERE id = ?''', (list_of_attributes[2], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET datum_zaniku = ? WHERE id = ?''', (list_of_attributes[3], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET priznak_kontextu = ? WHERE id = ?''', (list_of_attributes[4], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET rizeni_id_vzniku = ? WHERE id = ?''', (list_of_attributes[5], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET rizeni_id_zaniku = ? WHERE id = ?''', (list_of_attributes[6], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET ID_JE_1_PARTNER_BSM = ? WHERE id = ?''', (list_of_attributes[7], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET ID_JE_2_PARTNER_BSM = ? WHERE id = ?''', (list_of_attributes[8], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET ID_ZDROJ = ? WHERE id = ?''', (list_of_attributes[9], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET OPSUB_TYPE = ? WHERE id = ?''', (list_of_attributes[10], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET CHAROS_KOD = ? WHERE id = ?''', (list_of_attributes[11], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET ICO = ? WHERE id = ?''', (list_of_attributes[12], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET DOPLNEK_ICO = ? WHERE id = ?''', (list_of_attributes[13], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET NAZEV = ? WHERE id = ?''', (list_of_attributes[14], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET NAZEV_U = ? WHERE id = ?''', (list_of_attributes[15], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET RODNE_CISLO = ? WHERE id = ?''', (list_of_attributes[16], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET TITUL_PRED_JMENEM = ? WHERE id = ?''', (list_of_attributes[17], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET JMENO = ? WHERE id = ?''', (list_of_attributes[18], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET JMENO_U = ? WHERE id = ?''', (list_of_attributes[19], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET PRIJMENI = ? WHERE id = ?''', (list_of_attributes[20], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET PRIJMENI_U = ? WHERE id = ?''', (list_of_attributes[21], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET TITUL_ZA_JMENEM = ? WHERE id = ?''', (list_of_attributes[22], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET CISLO_DOMOVNI = ? WHERE id = ?''', (list_of_attributes[23], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET CISLO_ORIENTACNI = ? WHERE id = ?''', (list_of_attributes[24], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET NAZEV_ULICE = ? WHERE id = ?''', (list_of_attributes[25], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET CAST_OBCE = ? WHERE id = ?''', (list_of_attributes[26], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET OBEC = ? WHERE id = ?''', (list_of_attributes[27], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET OKRES = ? WHERE id = ?''', (list_of_attributes[28], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET STAT = ? WHERE id = ?''', (list_of_attributes[29], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET PSC = ? WHERE id = ?''', (list_of_attributes[30], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET MESTSKA_CAST = ? WHERE id = ?''', (list_of_attributes[31], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET CP_CE = ? WHERE id = ?''', (list_of_attributes[32], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET DATUM_VZNIKU2 = ? WHERE id = ?''', (list_of_attributes[33], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET RIZENI_ID_VZNIKU2 = ? WHERE id = ?''', (list_of_attributes[34], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET KOD_ADRM = ? WHERE id = ?''', (list_of_attributes[35], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET ID_NADRIZENE_PO = ? WHERE id = ?''', (list_of_attributes[36], list_of_attributes[0]))
            cur.execute(''' UPDATE OPSUB SET OS_ID = ? WHERE id = ?''', (list_of_attributes[37], list_of_attributes[0]))
            cur.execute("COMMIT TRANSACTION")
            cur.close()

        except conn.Error:
            print("failed!")
            cur.execute("ROLLBACK TRANSACTION")
            cur.close()
            conn.close()

    conn.close()
    return state_vector

# ======================================================================================================================
# Program mainline


def main():
    username = 'WSTEST'
    password = 'WSHESLO'
    endpoint = 'https://wsdptrial.cuzk.cz/trial/ws/ctios/2.8/ctios'  # access point to CTI_OS service
    db = os.path.join(os.path.dirname(__file__), 'Export_vse.db')  # db in the same directory as a script file

    posident_array = ['JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/qv/hZsqghT8/eZSkMbYPi4jB6kR9i3Ct3WAACH04hvU=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/ZUJpDsSCJ8SgzXg8HGLxDcrja3HYjJqkriDWY8SuLEY=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/SiXbDXGQb1+yo69gCeXApQQgighKtzcYijl2d9i+Ksc=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/AmxbLb+UwlDK6cmmPc8WNhC06DEL52zcEz2MKNel/fk=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/D9gXB8Z6J5ssEjdQMrPgCF608GKXU7Be3PfQkoEPUd4=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/MiEMrUe/U1ok4lICrsPOieZsG7sHwrvl9Sbju9kfJV8=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/RIE8id0peyYvmoNi15SoUjfnGR0L6dntbREQOPSoBvw=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/2tGtKCaIntTWQNhdRJ/6itaxruQMc7df7eUQoskngC4=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/sBkU4/Re91u/W+d1ev6I7dc4/ZzqEBFYvako7xmUu4U=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/Y6Tz5cyLC+k2K2sRnLgxhtqWYar0DFKSnqkKCuUEsrg=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/m7nZV7etTw+Rcj8rNpnldXFSjo22LeY7fxY38R0P7SQ=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/Nmu+7y7VMRHaCMgCOJf2reM7mvEivDBaNnEjcJEEIw4=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/c5ujO2BgWog9j4n7eK7tMx+Xz5CpFvsraY5S1LAsLBE=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/Nmu+7y7VMRHaCMgCOJf2reM7mvEivDBaNnEjcJEEIw4=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/c5ujO2BgWog9j4n7eK7tMx+Xz5CpFvsraY5S1LAsLBE=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/Nmu+7y7VMRHaCMgCOJf2reM7mvEivDBaNnEjcJEEI4=',
                      'JCwPjFIWzvmwkQd4LoMnRezX+OpG7AQQl0TgpEQz9AHRyF/Ar0dpY9DborLj7vG/c5ujO2BgWog9j4n7eK7tMx+Xz5CpFvsraY5S1LAsLE=']

    original_length = len(posident_array)
    posident_array = remove_duplicates(posident_array)  # remove duplicates from posidents array
    print('The length of posidents array without duplicates is {}'.format(len(posident_array)))
    number_of_duplicates = original_length - len(posident_array)

    max_num = 100 # max number of posidents inside one request
    print('Max number of posidents within one request is {}'.format(max_num))

    # create_log_file
    logging = create_log_file(os.path.dirname(__file__))

    # initialization
    uspesne_stazeno = 0
    neplatny_identifikator = 0
    opravneny_subjekt_neexistuje = 0
    expirovany_identifikator = 0
    state_vector = [neplatny_identifikator, expirovany_identifikator, opravneny_subjekt_neexistuje, uspesne_stazeno]

    if len(posident_array) <= max_num:
        request = draw_up_xml_request(username, password, posident_array)  # putting XML request together
        response = call_service(request, endpoint)  # CTI_OS request with upper parameters
        state_vector = save_attributes_to_db(response, db, state_vector, logging)  # parse and save attributes into DB
        logging.info('Pocet odstranenych duplicitnich posidentu: {}'.format(number_of_duplicates))
        logging.info('Zpracovano v ramci 1 pozadavku')

    else:
        full_arrays = math.floor(len(posident_array)/max_num)  # floor to number of full posidents arrays
        rest = len(posident_array) % max_num  # left posidents
        for i in range(0, full_arrays):
            start = i * max_num
            end = i * max_num + max_num
            posident_whole = posident_array[start: end]
            request = draw_up_xml_request(username, password, posident_whole)
            response = call_service(request, endpoint)
            state_vector = save_attributes_to_db(response, db, state_vector, logging)

        # make a request from the rest of posidents
        posident_rest = posident_array[len(posident_array) - rest: len(posident_array)]
        if posident_rest:
            request = draw_up_xml_request(username, password, posident_rest)
            response = call_service(request, endpoint)
            state_vector = save_attributes_to_db(response, db, state_vector, logging)
            divided_into = full_arrays + 1
        else:
            divided_into = full_arrays
        logging.info('Pocet odstranenych duplicitnich posidentu: {}'.format(number_of_duplicates))
        logging.info('Rozdeleno do {} pozadavku'.format(divided_into))

    logging.info('Pocet uspesne stazenych posidentu {} '.format(state_vector[3]))
    logging.info('Neplatny identifikator {}x.'.format(state_vector[0]))
    logging.info('Opravneny subjekt neexistuje {}x.'.format(state_vector[1]))
    logging.info('Expirovany identifikator {}x.'.format(state_vector[2]))


if __name__ == '__main__':
    main()



