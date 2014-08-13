#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Модуль содержит класс предназначенный для получения метеоданных с сайтов
http://www.meteoprog.ua, pogoda.by и rp5.ua
"""
from __future__ import unicode_literals

import urllib2
import datetime
import csv
import pylab
import os
import sys
import zipfile
import math
from bs4 import BeautifulSoup
import calendar
#from BeautifulSoup import BeautifulSoup

if sys.platform == "win32":
    sys.path.append(os.path.abspath("."))

#set line width
pylab.rcParams['lines.linewidth'] = 6
#set font size for titles
pylab.rcParams['axes.titlesize'] = 20
#set font size for labels on axes
pylab.rcParams['axes.labelsize'] = 20
#set size of numbers on x-axis
pylab.rcParams['xtick.major.size'] = 5
#set size of numbers on y-axis
pylab.rcParams['ytick.major.size'] = 5

#pylab.rcParams['text.usetex']=True
#pylab.rcParams['text.latex.unicode']=True

pylab.rcParams['text.usetex']=False
pylab.rcParams['font.sans-serif'] = ['Liberation Sans']
pylab.rcParams['font.serif'] = ['Liberation Serif'] 

class NotPage:
    pass

class MeteoStation(object):
    """
    Получение метеоданных. Базовый класс
    """
    def __init__(self):
        """
        city - город, например Dnipropetrovsk
        """
        # номера колонок в таблице
        self.tbody = [ "date",          # дата
                       "hour",
                       "min",
                       "precipitation", # осадки
                       "direct wind",   # направление ветера
                       "speed wind",    # скорость ветера
                       "temperature",   # температура
                       "humidity",      # Влажность
                       "presure",       # давление, мм.рт.ст.
                       "local presure", # местное давление
                       "local speed"	# местная скорость
                       ]      
        # данные
        self.table = {}
        for key in self.tbody:
            self.table[key] = []
    
    def local_press(self, sea_press, t, h=155.):
        """
        Приведение атмосферного давления к местным условиям 
        По умолчанию 155 м над уровнем моря для г. Днепропетровска
        http://pogoda.by/glossary/?nd=1
        """
        M = 0.029
        g = 9.81
        R = 8.314
        T = 273.15 + t
        return sea_press*math.exp(-M*g*h/(R*T))
    
    def local_speed(self, speed, h=10., hl=0.01):
        """
        Приведение скорости ветра к высоте hl
        """        
        return speed*(hl/h)**(1./5.)
    
    def parse(self, date):
        raise NotImplemented

    def save(self, fname):
        n = len(self.table[self.tbody[0]])
        with open(fname, "wb") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.tbody)
            for i in range(n):
                row = []
                for field in self.tbody:
                    try:
                        row.append(self.table[field][i].encode("utf-8"))
                    except AttributeError:
                        print "Couldn't convert value: ", self.table[field][i],\
                              " from field: ", field, " idx: ", i
                        row.append(str(self.table[field][i]).encode("utf-8"))
                writer.writerow(row)

    def parse_file(self, fname):
        raise NotImplemented

    def get_list(self, day, field):
        """
        Возвращает поле field для дня day
        """
        tempVal = []

        for idx, date in enumerate(self.table["date"]):
            syear, smonth, sday = date.split('-')
            d = datetime.datetime(year=int(syear), month=int(smonth), day=int(sday))
            #if syear == self.year and smonth == self.month and sday == day:
            if d == day:
                tempVal.append(self.table[field][idx])

        return tempVal

    def get(self, day, field, fnct=float):
        #print "Field: ", field
        #print "Day: ", day        
        idx = self.get_date_month().index(day)
        #print "Idx: ", idx
        #print self.table[field]
        param = fnct(self.table[field][idx])
        #for idx, date in enumerate(self.get_date_month()):
        #    #print date, self.table[field][idx]
        #    if date == day:                
        #        param = fnct(self.table[field][idx])
        #        break        
        return param        

    def get_avr_param(self, day, param):
        """
        Возвращает среднее значения параметра дня day
        """
        tempVal = map(float, self.get_list(day, param))
        try:
            return sum(tempVal)/float(len(tempVal))
        except:
            return None
            
    def get_extremum_field(self, field, extr=max):
        """
        Возвращает экстремум (max or min) значение параметра для всего периода
        """                        
        tempVal = map(float, self.table[field])
        extrVal = extr(tempVal)
        idxVal = tempVal.index(extrVal)        
        try:
            return (extrVal, idxVal)
        except:
            return None

    def get_temp(self, day):
        """
        Возвращает среднюю температуру дня day
        """
        tempVal = map(float, self.get_list(day, "temperature"))
        try:
            return sum(tempVal)/float(len(tempVal))
        except:
            return None

    def get_presure(self, day):
        """
        Возвращает среднюю температуру дня day
        """
        tempVal = map(float, self.get_list(day, "presure"))
        try:
            return sum(tempVal)/float(len(tempVal))
        except:
            return None

    def convert_date(self, dates, hours, minutes):
        """
        Преобразует дату в формат datetime.datetime
        """
        dateVal = []
        for idx, date in enumerate(dates):
            syear, smonth, sday = date.split('-')
            year  = int(syear)
            month = int(smonth)
            day   = int(sday)
            hour  = int(hours[idx])
            minute= int(minutes[idx])
            dateVal.append(datetime.datetime(year, month, day, hour, minute))

        return dateVal

    def get_date_day(self, day):
        '''
        Возвращает список содержащий время в формате datetime.datetime для дня day
        '''
        dates   = self.get_list(day, "date")
        hours   = self.get_list(day, "hour")
        minutes = self.get_list(day, "min")

        return self.convert_date(dates, hours, minutes)

    def get_date_month(self):
        """
        Возвращает список содержащий дату для текущего месяца в формате datetime.datetime
        """
        dates   = self.table["date"]
        hours   = self.table["hour"]
        minutes = self.table["min"]
        #print dates, hours, minutes
        return self.convert_date(dates, hours, minutes)

    def plot_temp(self, tempVal, aver_temp, dateVal, title, xlabel="Days", ylabel="Temperature", label="Temperature"):
        pylab.title(title)
        pylab.xlabel(xlabel)
        pylab.ylabel(ylabel)
        pylab.plot_date(dateVal, tempVal, 'b-', label=label)
        pylab.plot_date([min(dateVal), max(dateVal)], [aver_temp, aver_temp], 'r-', label="Average t="+str(round(aver_temp,2)))
        pylab.grid(True)
        pylab.legend(loc=0)
        pylab.show()

    def plot_temp_day(self, day):
        """
        Построение графика изменения температуры для дня day
        """
        tempVal = map(float, self.get_list(day, "temperature"))
        aver_temp = self.get_avr_param(day, "temperature")
        dateVal = self.get_date_day(day)
        title   = 'Day by Day Temperature in '+self.city+' in '+unicode(day.strftime("%d%B%Y"))
        self.plot_temp(tempVal, aver_temp, dateVal, title)

    def plot_temp_month(self):
        """
        Построение графика изменения температуры для текущего месяца
        """
        #print self.table["temperature"]
        tempVal = map(float, self.table["temperature"])
        aver_temp = sum(tempVal)/float(len(tempVal))
        dateVal = self.get_date_month()
        title   = 'Day by Day Temperature in '+self.city+' in '+self.date.strftime("%B")+' '+self.date.strftime("%Y")
        self.plot_temp(tempVal, aver_temp, dateVal, title)

    def plot_presure_day(self, day):
        """
        Построение графика изменения давления для дня day
        """
        tempVal = map(float, self.get_list(day, "presure"))
        aver_temp = self.get_avr_param(day, "presure")
        dateVal = self.get_date_day(day)
        title   = 'Day by Day Presure in '+self.city+' in '+day.strftime("%d")+' '+day.strftime("%B")+' '+day.strftime("%Y")
        self.plot_temp(tempVal, aver_temp, dateVal, title, "Hours", "Presure, mm.rt.st", "Presure by day")

    def plot_presure_month(self):
        """
        Построение графика изменения давления для текущего месяца
        """
        tempVal = map(float, self.table["presure"])
        aver_temp = sum(tempVal)/float(len(tempVal))
        dateVal = self.get_date_month()
        title   = 'Day by Day Presure in '+self.city+' in '+self.date.strftime("%B")+' '+self.date.strftime("%Y")
        self.plot_temp(tempVal, aver_temp, dateVal, title, "Days", "Presure, mm.rt.st", "Presyre by month")
        
    def plot_field(self, field, suffix="", out_dir=None):
        """
        Построение графика изменения параметра field
        """        
        tempVal = map(float, self.table[field])
        aver_temp = sum(tempVal)/float(len(tempVal))        
        dateVal = self.get_date_month()
        maxField, maxDateIdx = self.get_extremum_field(field)
        maxDate = dateVal[maxDateIdx]
        minField, minDateIdx = self.get_extremum_field(field, min)
        minDate = dateVal[minDateIdx]
        title   = 'Day by Day '+field.upper()+' in '+self.city+' in '+self.date.strftime("%B")+' '+self.date.strftime("%Y")
        #self.plot_temp(tempVal, aver_temp, dateVal, title)
        pylab.title(title)
        pylab.xlabel(r"Days")
        pylab.ylabel(field)
        pylab.plot_date(dateVal, tempVal, 'b-', label=field)
        pylab.plot_date([min(dateVal), max(dateVal)], [aver_temp, aver_temp], 'r-', label="Average "+str(round(aver_temp, 2)))
        pylab.grid(True)
        pylab.legend(loc=0)
        dt = dateVal[-1] - dateVal[0]
        df = maxField - minField
        #print dt.seconds
        offset = (datetime.timedelta(days=dt.days/20), df/50)
        #print offset
        arrowprops=dict(width=0.2, facecolor='black', shrink=0.05)
        
        posMax = (maxDate+offset[0], maxField+offset[1])
        pylab.annotate('max = '+str(round(maxField,2)), xy=(maxDate, maxField), 
                       xytext=posMax, arrowprops=arrowprops,
                       horizontalalignment='left', verticalalignment='bottom',)
        
        posMin = (minDate-offset[0], minField-offset[1])
        pylab.annotate('min = '+str(round(minField,2)), xy=(minDate, minField), 
                       xytext=posMin, arrowprops=arrowprops,
                       horizontalalignment='right', verticalalignment='top',)
        if out_dir is not None:            
            pylab.savefig(os.path.join(out_dir, field+"_"+suffix+".png"))
            pylab.close()
        else:
            pylab.show()

class MeteoProg(MeteoStation):
    """
    Получение метеоданных с сайте http://www.meteoprog.ua
    """
    def __init__(self, city="Dnipropetrovsk"):
        """
        city - город, например Dnipropetrovsk
        """
        MeteoStation.__init__(self)
        self.city = city
        # базовая страница (без года и месяца)
        self.mainpage = "http://www.meteoprog.ua/ru/fwarchive/"+city

    def parse(self, date):
        """
        Считывание данных может быть долгим т.к. это зависит от скорости
        соединения с интернет.
        Для усорения загрузки данных предназначен этот метод.
        Подготовка - считывание и парсинг данных с сайта http://www.meteoprog.ua
            year  - год,   например, 2013
            month - месяц, например, 01
        Результат записывается в словарь self.table
        """
        self.date = date
        self.year  = self.date.strftime("%Y") #year
        self.month = self.date.strftime("%m") #month
        days_of_month = calendar.monthrange(int(self.year), int(self.month))[1] # дней в месяце
        url = self.mainpage+"/"+self.year+"/"+self.month+"/dayofset/01-"+str(days_of_month)+"/"
        print url
        # парисм данные
        try:
            page = urllib2.urlopen(url)
            html = page.read()
        except:
            raise NotPage
        #print html
        soup = BeautifulSoup(html, from_encoding="utf-8")
        archive_table = soup.find("table", { "class" : "archive_table" })
        #print archive_table
        for tr in archive_table.findAll('tr'):
            #print tr
            n = 0 # номер колонки
            for td in tr.findAll('td'):
                #print n, self.tbody[n]
                self.table[self.tbody[n]].append(td.get_text())
                if self.tbody[n] == "temperature":
                    t = float(td.get_text())                    
                if self.tbody[n] == "presure":
                    pres = float(td.get_text())
                    self.table["local presure"].append(self.local_press(pres, t))
                if self.tbody[n] == "speed wind":
                    _td = td.get_text()
                    try:
                        speed = float(_td)
                    except ValueError:
                        print "Could not convert string ", _td, " to float"
                        speed = 0
                        #sys.exit(0)
                    self.table["local speed"].append(self.local_speed(speed))
                n+=1
        #print self.table           

class MeteoRP5(MeteoStation):
    """
    Получение данных с сайта http://rp5.ua
    Данные представлены в файле csv
    """
    def __init__(self):
        MeteoStation.__init__(self)
        enc = sys.getfilesystemencoding()
        self.csvfile = os.path.join(os.path.dirname(__file__).decode(enc), u"data.csv")
        #print self.csvfile
        self.csv = open(self.csvfile, 'rb')
        self.dialect = csv.Sniffer().sniff(self.csv.read(1024))
        self.city = "Dnipropetrovsk"

    def __del__(self):
        self.csv.close()

    def getMeteoprogOrSetDefault(self, day, param, default):
        print >> sys.stderr, "Try get from meteoprog.com.ua"
        mp = MeteoProg(city='Dnipropetrovsk')
        mp.parse(date=day)
        p = mp.get(day=day, field=param)
        if p is not None:
            print >> sys.stderr, "Succesfull: ", p
            date = p            
        else:
            print >> sys.stderr, "Failed: set to default "+default
            date = default
        
        self.table[param].append(date)
        t = mp.get(day=day, field="temperature")
        if param == "presure":
            lpres = self.local_press(date, t)
            self.table["local presure"].append(lpres)
        if param == "speed wind":
            lspeed = self.local_speed(date)
            self.table["local speed"].append(lspeed)
            
        pass

    def parse(self, date):
        """
        Парсинг данных из файла csv

        0. [Дата / Местное время] Время в данном населённом пункте. Учитывается летнее/зимнее время
        1. [T] Температура воздуха (градусы Цельсия) на высоте 2 метра над поверхностью земли
        2. [Po] Атмосферное давление на уровне станции (миллиметры ртутного столба)
        3. [P] Атмосферное давление, приведенное к среднему уровню моря (миллиметры ртутного столба)
        4. [Pa] Барическая тенденция: изменение атмосферного давления за последние три часа (миллиметры ртутного столба)
        5. [U] Относительная влажность (%) на высоте 2 метра над поверхностью земли
        6. [DD] Направление ветра (румбы) на высоте 10-12 метров над земной поверхностью, осредненное за 10-минутный период, непосредственно предшествовавший сроку наблюдения
        7. [Ff] Cкорость ветра на высоте 10-12 метров над земной поверхностью, осредненная за 10-минутный период, непосредственно предшествовавший сроку наблюдения (метры в секунду)
        8. [ff10] Максимальное значение порыва ветра на высоте 10-12 метров над земной поверхностью за 10-минутный период, непосредственно предшествующий сроку наблюдения (метры в секунду)
        9. [ff3] Максимальное значение порыва ветра на высоте 10-12 метров над земной поверхностью за период между сроками (метры в секунду)
        10.[N] Общая облачность
        11.[WW] Текущая погода, сообщаемая с метеорологической станции
        12.[W1] Прошедшая погода между сроками наблюдения 1
        13.[W2] Прошедшая погода между сроками наблюдения 2
        14.[Tn] Минимальная температура воздуха (градусы Цельсия) за прошедший период (не более 12 часов)
        15.[Tx] Максимальная температура воздуха (градусы Цельсия) за прошедший период (не более 12 часов)
        16.[Cl] Слоисто-кучевые, слоистые, кучевые и кучево-дождевые облака
        17.[Nh] Количество всех наблюдающихся облаков Cl или, при отсутствии облаков Cl, количество всех наблюдающихся облаков Cm
        18.[H] Высота основания самых низких облаков (м)
        19.[Cm]
        20.[Ch]
        21.[VV]
        22.[Td]
        23.[RRR]
        24.[tR]
        25.[E]
        26.[Tg]
        27.[E']
        28.[sss]
        """
        self.date  = date
        self.year  = self.date.strftime("%Y")#year
        self.month = self.date.strftime("%m")#month

        self.csv.seek(0) # переходим на начало
        spamreader = csv.reader(self.csv, dialect=self.dialect)
        for row in spamreader:
            #if row[0][0] != u'#' and row[0][0] !=u"М":
            if row[0][0].isdigit():
                #print row[0].split(" ")
                sdate, stime = row[0].split(' ')
                sday, smonth, syear = sdate.split('.')
                if date.month == int(smonth) and date.year == int(syear):
                    #print row[0].split(" ")
                    self.table["date"].append(syear+'-'+smonth+'-'+sday)
                    #print row[0]
                    shour, smin = stime.split(':')
                    self.table["hour"].append(shour)
                    self.table["min"].append(smin)
                    d = datetime.datetime(year=int(syear), month=int(smonth), day=int(sday), hour=int(shour), minute=int(smin))            
                    t = float(row[1])
                    self.table["temperature"].append(t)
                    try: # пробуем преобразовать в вещественное
                        pres = float(row[2])
                        self.table["presure"].append(pres)
                        lpres = self.local_press(pres, t)
                        self.table["local presure"].append(lpres)
                    except: # если ошибка - устанавливаем по умолчанию
                        print >> sys.stderr, row[0]
                        print >> sys.stderr, "Can't convert "+row[2]+" to float"
                        self.getMeteoprogOrSetDefault(day=d, param="presure", default=750.)
                    try:
                        self.table["humidity"].append(float(row[5]))
                    except:
                        print >> sys.stderr, row[0]
                        print >> sys.stderr, "Can't convert "+row[5]+" to float"
                        self.getMeteoprogOrSetDefault(day=d, param="humidity", default=100.)
                        #self.table["humidity"].append(100.)
                    self.table["direct wind"].append(row[6])
                    speed = float(row[7])
                    self.table["speed wind"].append(speed)
                    lspeed = self.local_speed(speed)
                    self.table["local speed"].append(lspeed)
                else:
                    if date.year > int(syear) and date.month > int(smonth):
                        #print "break at : ", syear, "/", smonth
                        break
                    else:
                        continue
                        
class PogodaBy(MeteoStation):
    def __init__(self):
        MeteoStation.__init__(self)
        self.dsource = "pogoda.by" # пака с данными
        self.city = "Dnipropetrovsk"
    
    def zip_name(self, year, month):
        syear = str(year)
        smonth = str(month)        
        if month < 10:
            smonth = "0"+str(month)
        enc = sys.getfilesystemencoding()
        curplace = os.path.dirname(__file__).decode(enc)
        fname = os.path.join(curplace, self.dsource, syear+"_"+smonth+".zip")
        return fname
    
    def has_local_date(self, year, month):
        """
        Проверяет наличие файла данных
        """        
        zip_file = self.zip_name(year, month)
        if os.path.isfile(zip_file):
            return True
        else:
            return False
    
    def download_data(self, year, month):
        syear = str(year)
        smonth = str(month)
        if month < 10:
            smonth = "0"+str(month)
        base_url = "http://pogoda.by/zip/"
        citi_code = "34504"
        url = base_url+syear+"/"+citi_code+"_"+syear+"-"+smonth+".zip"
        zip_name = self.zip_name(year, month)
        zipfile = urllib2.urlopen(url)

        with open(zip_name, 'w') as f: 
            f.write(zipfile.read())        
    
    def unzip(self, year, month):
        zip_name = self.zip_name(year, month)
        zfile = zipfile.ZipFile(zip_name, "r")
        csv_file = zfile.namelist()[0]
        try:
            data = zfile.read(csv_file)
        except KeyError:
            print ('ERROR: Did not find %s in zip file' % csv_file)
        else:            
            return data.decode("cp1251")        
    
    def fnct_speed(self, date):
        s = unicode(date)        
        if s == u"Штиль":
            return 0
        else:
            return float(s)
    
    def parse(self, date):
        year = date.year
        month = date.month        
        day = date.day
        self.date = date
        if not self.has_local_date(year, month):
            print ("Download data from pogoda.by...")
            self.download_data(year, month)
        
        if self.has_local_date(year, month):
            data = self.unzip(year, month)            
            for line in data.split('\n'):
                row = line.split(";")
                smonth = date.strftime("%m")
                sday = row[0]
                self.table["date"].append(str(year)+'-'+smonth+'-'+sday)
                shour = str(row[1])
                if float(row[1]) > 9:
                    shour = "0"+str(row[1])
                self.table["hour"].append(shour)
                self.table["min"].append("00")
                temp = row[2].replace(",", ".")
                self.table["temperature"].append(temp)
                direct = row[3]
                self.table["direct wind"].append(direct)
                speed = row[4]
                self.table["speed wind"].append(speed)
                humid = row[8]
                self.table["humidity"].append(humid)
                pres = row[9]
                self.table["presure"].append(pres)
                lpres = self.local_press(float(pres), float(temp))
                self.table["local presure"].append(lpres*0.75) # из гПа в мм. рт. ст.
                lspeed = self.local_speed(self.fnct_speed(speed))
                self.table["local speed"].append(lspeed)

def testPogodaBy():
    md = PogodaBy()
    assert md.has_local_date(2011, 01)
    day = datetime.datetime(year=2011, month=1, day=1, hour=0)
    step = datetime.timedelta(hours=3)
    md.parse(day)
    for temp in [-4.6, -8.6, -2.4, -1.2, -0.6, -1.7, -3.3, -2.8, 
                 -2.3, -1.7, -3.1, -1.5, 1.0, -2.6, -3.9, -4.2]:
        assert md.get(day, "temperature") == temp
        day += step
    for speed in [3, 3, 0, 0, 3, 3, 3, 3,
                  5, 5, 4, 5, 6, 5, 6, 5]:
        assert speed  == md.get(day, "speed wind", md.fnct_speed)        
        #if s == u"Штиль":
        #    assert speed == 0
        #else:
        #    assert speed == float(s)
        day += step        
    for press in [1026, 1027, 1028, 1030, 1031, 1032, 1033, 1034,
                  1034, 1034, 1035, 1035, 1034, 1034, 1034, 1034]:        
        assert press == md.get(day, "presure")
        day += step
    
    md = PogodaBy()
    for i in range(1, 13):
        day = datetime.datetime(year=2012, month=i, day=1, hour=0)
        md.parse(day)
    #md.plot_temp_month()
    # проверяем пропущенные значения
    dates = []
    for date in md.get_date_month():
        dates.append(date)
    for i in range(1, len(dates)):
        if dates[i] - dates[i-1] > step:
            print dates[i], dates[i-1]

    md.plot_field("local presure")
    md.plot_field("temperature")
   
def test():
    mp = MeteoProg(city='Dnipropetrovsk')
    #mp = MeteoRP5()
    for i in range(11):
        day = datetime.datetime(year=2010, month=i+1, day=1)
        mp.parse(date=day)
    mp.save("meteoprog.ua/meteoprog.csv")
    #print mp.get_temp(day=day)
    step = datetime.timedelta(days=1)
    #mp.plot_temp_day(day=day)
    mp.plot_temp_month()

if __name__ == "__main__":
    test()
    testPogodaBy()
