#!/usr/bin/env python
# -*- coding: utf8 -*-
import __future__
import urllib2

def download_data(year, month):
    """
    http://pogoda.by/zip/2011/34504_2011-01.zip
    """
    base_url = "http://pogoda.by/zip/"
    citi_code = "34504"
    url = base_url+year+"/"+citi_code+"_"+year+"-"+month+".zip"
    zip_name = year+"_"+month+".zip"
    zipfile = urllib2.urlopen(url)

    with open(zip_name, 'w') as f: 
        f.write(zipfile.read())

       
if __name__ == "__main__":
    year = "2011"
    for month in range(1, 13):
        if month >= 10:
            download_data(year, str(month))
        else:
            download_data(year, "0"+str(month))
