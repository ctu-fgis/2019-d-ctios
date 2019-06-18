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
import re


def remove_duplicates(array):
    """
    Remove duplicates in array
    :param array: array of POSIdents
    :type array: list
    :returns response: array of POSIdents without duplicates
    :rtype response: list
    """
    return list(dict.fromkeys(array))


def draw_up_xml_request(path, array):
    """
    Put together a request in the XML form to CTI_OS service
    :param path: path to XML request
    :type path: string
    :param array: array of POSIdents without duplicates
    :type array: list
    :returns response: final XML request with all POSIdents attributes
    :rtype response: list
    """

    try:
        with open(path) as file:  # Use file to refer to the file object

            request = file.read()

            j = 0
            for i in array:
                root = et.fromstring(request)
                body = root.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}CtiOsRequest')
                id_tag = et.Element('{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent')
                id_tag.text = i
                body.insert(1, id_tag)
                request = et.tostring(root, encoding="unicode")
                j = j+1
            return request

    except Exception:
        logging.exception('SPATNA CESTA K VSTUPNIMU XML SOUBORU')
        raise Exception("CANNOT FIND XML FILE {}".format(path))


def call_service(request, endpoint):
    """
    Send a request in the XML form to CTI_OS service
    :param request: XML request to CTI_OS service
    :type request: string
    :param endpoint: end address of CTI_OS service
    :type endpoint: string
    :raises: '3xx Redirect', '4xx Client Error', '5xx Server Error'
    :returns response: XML file with all POSIDENT attributes
    :rtype response: string
    """
    headers = {'Content-Type': 'text/xml;charset=UTF-8',
               'Accept-Encoding': 'gzip,deflate',
               'SOAPAction': "http://katastr.cuzk.cz/ctios/ctios",
               'Connection': 'Keep-Alive'}

    response = requests.post(endpoint, data=request, headers=headers)
    status_code = response.status_code
    response = response.text

    if 300 <= status_code < 400:
        logging.fatal('STAVOVY KOD HTTP 3xx: REDIRECT')
        raise Exception("3xx Redirect\n")
    elif 400 <= status_code < 500:
        logging.fatal('STAVOVY KOD HTTP 4xx: CLIENT ERROR!')
        raise Exception("4xx Client Error\n" + request)
    elif 500 <= status_code < 600:
        logging.fatal('STAVOVY KOD HTTP 5xx: SERVER ERROR!')
        raise Exception("5xx Server Error\n" + request)
    else:
        logging.info('STAVOVY KOD HTTP 2xx: SUCCESS!')
        return response


def create_connection(db_file):
    """
    Create a database connection to the SQLite database specified by the db_file
    :param db_file: path to database file
    :type db_file: string
    :raises: 'SQLITE3 ERROR'
    :returns conn: Connection object
    :rtype conn: Connection object
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error:
        logging.fatal('SQLITE3 ERROR!')
        raise Exception("SQLITE3 ERROR" + db_file)


def create_log_file(log_path):
    """
    Create log file
    :param log_path: path to log file
    :type log_path: string
    :returns logging: Logging object
    :rtype conn: Logging object
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


def transform_names(xml_name):
    """
    Convert names in XML name to name in database (eg. StavDat to stav_dat)
    :param xml_name: given names from XML format
    :type xml_name: string
    :returns database_name: column names in database OPSUB
    :rtype database_name: string
    """
    database_name = re.sub('([A-Z]{1})', r'_\1', xml_name).upper()
    return database_name


def transform_names_dict(xml_name, dictionary):
    """
    Convert names in database to name in XML based on special dictionary
    :param xml_name: given names from XML format
    :type xml_name: string
    :param dictionary:
    :type dictionary: dictionary
    :returns database_name: column names in database OPSUB
    :rtype database_name: string
    """
    # key = name in XML
    # value = name in database

    try:
        database_name = dictionary[xml_name]
        return database_name
    except Exception:
        logging.exception('JMENO V XML DOKUMENTU NELZE PREVEST NA JMENO SLOUPCE V SQLITE DATABAZI')
        raise Exception("XML ATRIBUTE NAME CANNOT BE CONVERTED TO DATABASE COLUMN NAME")


def save_attributes_to_db(response, db_file, state_vector, logging, dictionary):
    """
    1. Parses XML returned by CTI_OS service into desired parts which will represent database table attributes
    2. Connects to Export_vse.db
    3. Alters table by adding OS_ID column if not exists
    4. Updates attributes for all posidents in SQLITE3 table rows
    Keyword arguments: xml file returned by CTI_OS service, path to the database file and state information vector, logging
    Returns: failed! if problem appears otherwise updated state vector
    """

    root = et.fromstring(response)

    for os in root.findall('.//{http://katastr.cuzk.cz/ctios/types/v2.8}os'):

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
        else:
            state_vector[3] = state_vector[3] + 1  # no error

        # Parse XML returned by CTI_OS service into desired parts
        # create the dictionary, where will be XML child attribute names and particular texts
        xml_attributes = {}
        database_attributes = {}

        for child in os:
            name = child.tag
            if name == '{http://katastr.cuzk.cz/ctios/types/v2.8}pOSIdent':
                pos = os.find(name)
                posident = pos.text
            if name == '{http://katastr.cuzk.cz/ctios/types/v2.8}osId':
                o = os.find(name)
                osid = o.text

        for child in os.find('.//{http://katastr.cuzk.cz/ctios/types/v2.8}osDetail'):
            name2 = child.tag
            xml_attributes[child.tag[child.tag.index('}') + 1:]] = os.find('.//{}'.format(name2)).text

        # Find out the names of columns in database and if column os_id doesnt exist, add it
        try:
            conn = create_connection(db_file)
            cur = conn.cursor()
            cur.execute("PRAGMA read_committed = true;")
            cur.execute('select * from OPSUB')
            col_names = list(map(lambda x: x[0], cur.description))
            if 'OS_ID' not in col_names:
                cur.execute('ALTER TABLE OPSUB ADD COLUMN OS_ID TEXT')
            cur.close()
        except conn.Error:
            cur.close()
            conn.close()
            logging.exception('Pripojeni k databazi selhalo')
            raise Exception("CONNECTION TO DATABSE FAILED")

        #  Transform xml_names to database_names
        for xml_name, xml_value in xml_attributes.items():
            database_name = transform_names(xml_name)
            if database_name not in col_names:
                database_name = transform_names_dict(xml_name, dictionary)
            database_attributes.update({database_name: xml_value})

        #  Update table OPSUB by database_attributes items
        try:
            cur = conn.cursor()
            cur.execute("BEGIN TRANSACTION")
            for dat_name, dat_value in database_attributes.items():
                cur.execute("""UPDATE OPSUB SET {0} = ? WHERE id = ?""".format(dat_name), (dat_value, posident))
            cur.execute("""UPDATE OPSUB SET OS_ID = ? WHERE id = ?""", (osid, posident))
            cur.execute("COMMIT TRANSACTION")
            cur.close()
            logging.info('Radky v databazi u POSIdentu {} aktualizovany'.format(posident))
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

    # all these things need to have in the same directory
    path = os.path.join(os.path.dirname(__file__), 'request.xml')  # xml without posidents
    db = os.path.join(os.path.dirname(__file__), 'Export_vse.db')  # db in the same directory as a script file
    posidents = os.path.join(os.path.dirname(__file__), 'posidents.txt')  # the list of posidents in text file

    # create_log_file
    logging = create_log_file(os.path.dirname(__file__))

    try:
        with open(posidents) as text_file:

            posident_array = text_file.read().split(',')

    except Exception:
        logging.exception('TEXTOVY SOUBOR S POSIDENTY NENALEZEN')
        raise Exception("BAD PATH TO POSIDENT ARRAY FILE")

    original_length = len(posident_array)
    logging.info('Puvodni pocet POSIdentu v seznamu: {}'.format(original_length))

    posident_array = remove_duplicates(posident_array)  # remove duplicates from posidents array
    logging.info('Delka seznamu POSIdentu po odstraneni duplicitnich zaznamu: {}'.format(len(posident_array)))
    number_of_duplicates = original_length - len(posident_array)
    logging.info('Pocet duplicitnich zaznamu: {}'.format(number_of_duplicates))

    max_num = 100  # max number of posidents inside one request
    logging.info('Maximalni pocet POSIdentu v ramci jednoho pozadavku na sluzbu: {}'.format(max_num))

    # dictionary with relevant names in xml and database
    dictionary = {'priznakKontext': 'PRIZNAK_KONTEXTU',
                  'partnerBsm1': 'ID_JE_1_PARTNER_BSM',
                  'partnerBsm2': 'ID_JE_2_PARTNER_BSM',
                  'charOsType': 'CHAROS_KOD',
                  'kodAdresnihoMista': 'KOD_ADRM',
                  'idNadrizenePravnickeOsoby': 'ID_NADRIZENE_PO'}

    # initialization
    uspesne_stazeno = 0
    neplatny_identifikator = 0
    opravneny_subjekt_neexistuje = 0
    expirovany_identifikator = 0
    state_vector = [neplatny_identifikator, expirovany_identifikator, opravneny_subjekt_neexistuje, uspesne_stazeno]
    endpoint = 'https://wsdptrial.cuzk.cz/trial/ws/ctios/2.8/ctios'  # access point to CTI_OS service

    if len(posident_array) <= max_num:
        request = draw_up_xml_request(path, posident_array)  # putting XML request together
        response = call_service(request, endpoint)  # CTI_OS request with upper parameters
        state_vector = save_attributes_to_db(response, db, state_vector, logging, dictionary)  # parse and save attributes into DB
        logging.info('Zpracovano v ramci 1 pozadavku')

    else:
        full_arrays = math.floor(len(posident_array)/max_num)  # floor to number of full posidents arrays
        rest = len(posident_array) % max_num  # left posidents
        for i in range(0, full_arrays):
            start = i * max_num
            end = i * max_num + max_num
            posident_whole = posident_array[start: end]
            request = draw_up_xml_request(path, posident_whole)
            response = call_service(request, endpoint)
            state_vector = save_attributes_to_db(response, db, state_vector, logging, dictionary)

        # make a request from the rest of posidents
        posident_rest = posident_array[len(posident_array) - rest: len(posident_array)]
        if posident_rest:
            request = draw_up_xml_request(path, posident_rest)
            response = call_service(request, endpoint)
            state_vector = save_attributes_to_db(response, db, state_vector, logging, dictionary)
            divided_into = full_arrays + 1
        else:
            divided_into = full_arrays
        logging.info('Rozdeleno do {} pozadavku'.format(divided_into))

    logging.info('Pocet uspesne stazenych posidentu: {} '.format(state_vector[3]))
    logging.info('Neplatny identifikator: {}x.'.format(state_vector[0]))
    logging.info('Opravneny subjekt neexistuje: {}x.'.format(state_vector[1]))
    logging.info('Expirovany identifikator: {}x.'.format(state_vector[2]))


if __name__ == '__main__':
    main()



