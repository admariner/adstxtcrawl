import sys
import time
import csv
import sqlite3
import logging
from optparse import OptionParser
import re
from datetime import datetime
from tld import get_tld

#pip install requests
import requests

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse


def load_url_queue(csv_domain_list, domain_queue):
    
    row_count = 0

    with open(csv_domain_list) as csvfile:
        print ('Reading Domains from csv')
        domains = csv.reader(csvfile, delimiter=',', quotechar='|')

        for domain in domains:
            
            try:
                domain[0] = 'http://{d}'.format(d=domain[0])
                host = get_tld(domain[0], as_object=True)
                host = host.fld
            except:
                host = domain[0]

            domain_queue[row_count] = host
            
            row_count += 1    
    print ('Stored URLs and Domains in a variable.')   

    return row_count


def storing_data_to_database (connection, domain_queue):

    row_count = 0

    myheaders = {
        'User-Agent': 'AdxTxtCrawler/1.0; +Siddesh Test',
        #'User-Agent': 'Mediapartners-Google',
        #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36'),
        'Accept'    : 'text/plain',
    }

    domain_queue = set(domain_queue.values())

    for domain in domain_queue:

        current_url = 'http://{host}/ads.txt'.format(host=domain)
        print (current_url)

        # if we can't connect, then move on
        try:
            response = requests.get(current_url, headers=myheaders, allow_redirects=True, timeout=2)

        except requests.exceptions.RequestException as e:
            # log warnings in db and also count of errors - error_domain_count
            logging.warning(e)
            continue

        # Checking for redirects/http errors/content        
        # disallow anything where response history > 3
        if (len(response.history) > 3):
            #error_log (connection, domain_name, data_row = None, comment, line_number = None, 'too many redirects.')
            logging.warning("too many redirects.")
            continue

        # HTML or js content, skipping
        if (re.search('^([^,]+,){2,3}?[^,]+$', response.text, re.MULTILINE) is None):
            logging.warning("schema inappropriate, skipping")
            continue

        if ('<html' in response.text or '<script' in response.text):
            logging.warning("html or js content, skipping")
            continue

        temp_file = 'temp_file.csv'
        with open(temp_file, 'wb') as t:
            t.write(response.text.encode())
            t.close()

        with open(temp_file, 'r') as t:
            #read the line, split on first comment and keep what is to the left (if any found)
            line_reader = csv.reader(t, delimiter='#', quotechar='|')
            comment = ''

            line_number = 1
            for line in line_reader:
                try:
                    data_line = line[0]
                except:
                    data_line = ""

                data_reader = csv.reader([data_line], delimiter=',', quotechar='|')

                for row in data_reader:
                    if len(row) > 0 and row[0].startswith( '#' ):
                        continue

                    if (len(line) > 1) and (len(line[1]) > 0):
                         comment = line[1]

                    row_count = row_count + processing_row_to_database(connection, row, comment, domain, line_number)
                    line_number += 1

    return row_count


def processing_row_to_database(connection, data_row, comment, domain_name, line_number):

    #(domain_name,advertiser_domain,publisher_id, account_type,cert_authority_id,line_number,is_valid_syntax,raw_string) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"

    domain_name       = domain_name
    advertiser_domain = ''
    publisher_id      = ''
    account_type      = ''
    raw_string        = ','.join(data_row)

    if len(data_row) >= 3:
        advertiser_domain  = data_row[0].lower()
        publisher_id       = data_row[1].lower()
        account_type       = data_row[2].lower()

    cert_authority_id = data_row[3].lower() if len(data_row) == 4 else ''
    #data validation
    data_valid = 1

    # Minimum length of a domain name is 1 character, not including extensions.
    # Domain Name Rules - Nic AG
    # www.nic.ag/rules.htm
    if(len(domain_name) < 3):
        data_valid = 0

    if(len(advertiser_domain) < 3):
        data_valid = 0

    # could be single digit integers
    if(len(publisher_id) < 1):
        data_valid = 0

    # ads.txt supports 'DIRECT' and 'RESELLER'
    if(len(account_type) < 6):
        data_valid = 0

    if (data_valid > 0):
        # Insert a row of data using bind variables (protect against sql injection)
        c = connection.cursor()
        insert_stmt = "INSERT INTO ads_txt (domain_name, advertiser_domain, publisher_id, account_type, cert_authority_id, line_number, raw_string) VALUES (?,?,?,?,?,?,?);"
        c.execute(insert_stmt, (domain_name, advertiser_domain, publisher_id, account_type, cert_authority_id, line_number, raw_string,))


        data = c.fetchall()
        try:
            if not data:
                connection.commit()
        except sqlite3.Error as e:
            print(f"Database error: {' '.join(e.args)}")
        except Exception as e:
            print(f"Exception in _query: {e}")

        # Save (commit) the changes
        connection.commit()
        return 1

    return 0


def error_log(connection, domain_name, data_row, comment, line_number, error_message):
    insert_stmt = "INSERT INTO ads_txt_error_logs (domain_name, error_message) VALUES (?,?);"
    c = connection.cursor()
    c.execute(insert_stmt, (domain_name, error_message,))

    data = c.fetchall()
    try:
        if not data:
            connection.commit()
    except sqlite3.Error as e:
        print(f"Database error: {' '.join(e.args)}")
    except Exception as e:
        print(f"Exception in _query: {e}")

    #(1,domain_name,advertiser_domain,publisher_id, account_type,cert_authority_id,1,1,data_row,datetime.now(),datetime.now()))

    # Save (commit) the changes
    connection.commit()



### MAIN Function ###

start_time = time.time()

logging.warning("Siddesh")

domain_queue = {}
csv_domain_list = 'domain_lists.csv'
connection = None
total_domain_count = 0
valid_domain_count = 0
error_domain_count = 0
total_time_taken   = 0
average_time_taken = 0


total_domain_count = load_url_queue(csv_domain_list ,domain_queue)


if total_domain_count > 0:
    connection = sqlite3.connect('test.db')
    print ('Database Connected')

with connection:
    #create_stmt = "create table ads_txt (        row_id integer NOT NULL PRIMARY KEY AUTOINCREMENT, domain_name varchar(100) NOT NULL,        advertiser_domain varchar(100),        publisher_id int(50),        account_type varchar(100),        cert_authority_id varchar(100),        line_number int(10),        is_valid_syntax tinyint(1) DEFAULT 0,        raw_string varchar(200),        creation_date datetime DEFAULT CURRENT_TIMESTAMP,        updation_date datetime DEFAULT CURRENT_TIMESTAMP    );"
    #c = connection.cursor()
    #c.execute(create_stmt)
    print('Table Created')
    valid_domain_count = storing_data_to_database (connection, domain_queue)
    if(valid_domain_count > 0): 
        connection.commit()

connection.close()
print ('Database Connection Closed.')       

end_time = time.time()

print(f'Total Number of Domains: {str(total_domain_count)}')
print(f'Total Number of Entries Added: {str(valid_domain_count)}')
print(f'Start Time: {time.asctime(time.localtime(start_time))}')
print(f'End Time: {time.asctime(time.localtime(end_time))}')
print(f'Total Time Taken: {str(end_time-start_time)}')