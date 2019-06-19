#!/usr/local/bin/python3.7
"""
Mobile Spidey
Crawl app-ads.txt
import all the requests modules
"""
import requests
import pandas as pd
import sys
import csv
import re

NAME_INDEX, REL_TYPE_INDEX = 0, 2


"""
Given input of names, bundle id's and os, retrieve and interpret the app-ads.txt file for each app.
Goal is to identify whether TripleLift is listed, and if so listed properly, in the mobile equivalent
of ads.txt for app publishers.

app-ads.txt info and givens based on https://iabtechlab.com/wp-content/uploads/2019/03/app-ads.txt-v1.0-final-.pdf
"""


def get_url(bundle, os):
    url = None
    if os == 'ios':
        store_url = 'http://itunes.apple.com/us/lookup?id=%s' % bundle
        # Get '1.txt' from itunes store, process result to grab sellerUrl, grab ad.txt from domain/sellerUrl
        try:
            response = requests.get(store_url)
            payload = response.json()
            if payload:
                results = payload['results'][0]
                if results['sellerUrl']:
                    url = results['sellerUrl']
                    print(f'Huzzah! The iOS app url is {url}!\n')
        except Exception as err:
            print(f'Other error occurred: {err}')
    elif os == 'android':
        store_url = 'https://play.google.com/store/apps/details?id=%s' % bundle
        try:
            response = requests.get(store_url)
            rawurl = re.search('appstore:developer_url.*>', response.text)
            if rawurl:
                rawurl = rawurl[0]
                # print(rawurl[0])
                url = re.search('\"http[^\"]+\"', rawurl)[0].strip('\"')
                print(f'Huzzah! The Android app url is {url}!')
        except Exception as err:
            print(f'Other error occurred: {err}')
    else:
        print('Invalid OS - send \"ios\" or \"android\"\n')
    return url
    """
    ANDROID LOGIC - GRAB SELLERURL FROM PLAYSTORE
    elif os == 'android':
        #android logic
        store_url = 'https://play.google.com/store/apps/details?id=%s' % bundle
        try:
            response = requests.get(store_url)
            url = response.json()['results'][0]['sellerUrl']
            # df = pandas.read_json('1.txt')  # parse txt file json returned from apple store using pandas
            # url = df['results'][0]['sellerUrl']
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')
        else:
            print('Huzzah! The app url is %s!' % url)
        return url
    """


def get_app_ads_text(app_url):
    if app_url[-1] == '/':
        ads_url = app_url + 'app-ads.txt'
    else:
        ads_url = app_url + '/' + 'app-ads.txt'
    listed_pub_id, tl_rel_type = None, 'no_app_ads_txt'
    try:
        response = requests.get(ads_url)
        # check if ads txt returned, and if so turn it into a row-readable csv parser
        if response.status_code == 200 and '<head>' not in response.text:
            if any(term in response.text for term in ['DIRECT', 'RESELLER']):
                # print(response.text + '\n')
                for row in response.text.splitlines():
                    # print(row)
                    if 'triplelift' in row:
                        row = row.split(',')
                        listed_pub_id = row[1].strip(' ')
                        tl_rel_type = row[2].strip(' ')
                        # print(app_url,'triplelift',row[1],tl_rel_type)
                        return listed_pub_id, tl_rel_type
                print('actually not listed in app-ads.txt')
                tl_rel_type = 'Unlisted'
            else:
                print('response text looks different..')
                print(response.text)
    except Exception as err:
        print(f'Error in adstxt getter: {err}')
    return listed_pub_id, tl_rel_type


"""
Return the relationship type/status of Triplelift in the app publisher's app-ads.txt file.
triplelift.com, 3410, DIRECT, 6c33edb13117fd86 => 'DIRECT'
xad.com, 767, RESELLER, 81cbf0a75a5e0e9a => 'Unlisted'
triplelift.com, 1190, RESELLER, 81cbf0a75a5e0e9 => 'RESELLER'
"""


if __name__ == '__main__':
    print('Starting mobile ads.txt crawler')
    # set up csv parsers to ingest and write out results
    filename = 'mobileapplist.csv'
    if len(sys.argv) > 1:
        if sys.argv[1][-4:-1] == 'csv':
            filename = sys.argv[1]
    df = pd.read_csv(filename)
    # df.info()
    writer = open('mobile_crawler_results.csv', 'w')
    cwriter = csv.writer(writer)
    headers = ['name', 'bundle_id', 'os', 'app_url', 'listed_pub_id', 'tl_rel_type']
    cwriter.writerow(headers)
    # # start reading in and processing app bundle tuples
    for index,row in df.iterrows():
        name, orig_pub_id, bundle, os = row[0], row[1], row[2], row[3]
        print(name, orig_pub_id, bundle, os)
        app_url, listed_pub_id, tl_rel_type = None, None, 'no_url'
        # get app_url/sellerDomain
        app_url = get_url(bundle, os)
        if not app_url:
            # url empty, tl_relationship 'no_url'
            outrow = [name, orig_pub_id, bundle, os, app_url, listed_pub_id, tl_rel_type]
            cwriter.writerow(outrow)
            # proceed to next row, no url to use
            continue
        # assume no ads.txt
        listed_pub_id, tl_rel_type = get_app_ads_text(app_url)
        if not listed_pub_id:
            # pub id empty or tl_relationship/account not in {direct,reseller}
            outrow = [name, orig_pub_id, bundle, os, app_url, listed_pub_id, tl_rel_type]
            cwriter.writerow(outrow)
            # proceed to next row, no url to use
            continue
        outrow = [name, orig_pub_id, bundle, os, app_url, listed_pub_id, tl_rel_type]
        print(outrow)
        cwriter.writerow(outrow)
        print('Woohoo! Found TL in app-ads.txt!\n')
    #     cwriter.writerow(name, bundle, os, app_url, tl_rel_type)
    #     print('App %s has bundle id \"%s\", domain url \"%s\", and ads.txt status of %s' % (name,bundle_id,app_url,tl_rel_type))
    print('Finished crawling %d records')
