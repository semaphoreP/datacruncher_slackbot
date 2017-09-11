from datetime import datetime
import pytz as tz
import astropy.time

gemini_longitude = -70 - 44/60. - 12.096/3600

all_timezones = tz.common_timezones
all_abbreviations = {} # convert from abbreviation to full time zone
for zone in all_timezones:
    # santaigo gets CLT
    if zone == "America/Santiago":
        abbrev = "CLT"
    else:
        abbrev = tz.timezone(zone).localize(datetime.now()).strftime('%Z')

    # still check to make sure no one takes over this abbreviation
    if abbrev == 'CLT' or abbrev == 'CLST' or abbrev == 'CLDT':
        if 'Santiago' not in zone:
            continue
        else:
            # make sure it is CLT
            abbrev = 'CLT'

    all_abbreviations[abbrev] = zone

def get_timezone(tz_abbrev):
    """
    Convert form time zone abbrevaiton (3 characeters) to full time zone
    """
    new_tz_abbrev = tz_abbrev
    
    # correct daylight savings
    #if len(new_tz_abbrev) == 3:
    #    # check for daylight savings
    #    if new_tz_abbrev.upper()[1] == u'D':
    #        dst = True
    #        # check to make sure the lookup is this version
    #        # else switch abbreviation to standard time
    #        if not new_tz_abbrev in all_abbreviations:
    #            new_tz_abbrev = new_tz_abbrev[0] + u'S' + new_tz_abbrev[2]
    #    else:
    #        dst = False
    #        # check to make sure the lookup is this version
    #        # else switch abbreviation to DST time
    #        if not new_tz_abbrev in all_abbreviations:
    #            new_tz_abbrev = new_tz_abbrev[0] + u'D' + new_tz_abbrev[2]
    
    # correct UT to UTC
    if new_tz_abbrev.upper() == u'UT':
        new_tz_abbrev = u'UTC'
    
    # no need to look up UTC
    if new_tz_abbrev.upper() == u'UTC':
        timezone = tz.timezone('UTC')   
    else:       
        try:    
            timezone = tz.timezone(all_abbreviations[new_tz_abbrev])
        except KeyError:
            timezone = None
    return timezone
    


def convert_time(time_str, zone_from, zone_to):
    """
    Args:
        time_str: "HH:MM"
    """
    # figure out time zones
    tz_from = get_timezone(zone_from)
    tz_to = get_timezone(zone_to)
    
    if tz_from is None or tz_to is None:
        return None
    
    # parse input time
    time_str_args = time_str.split(":")
    hours = int(time_str_args[0])
    min = int(time_str_args[1])
    print(hours, min)
    
    # since date is unknown, grab today's date
    time = datetime.now()
    time = datetime(time.year, time.month, time.day, hours, min, tzinfo=tz_from)
    
    fmt = "%I:%M %Z%z"
    new_time = time.astimezone(tz_to)
    return new_time.strftime(fmt)
    

def get_time_now(mytz):
    """
    Get current time in this time zone.  Also supports LST, JD, and MJD
    
    Args:
        mytz: abbrevation e.g. CLT
    """
    if mytz.upper() == 'LST':
        return get_lst(gemini_longitude) + " (Gemini South)"
    
    if mytz.upper() == 'JD'or mytz.upper() == 'MJD':
        return get_jd(modified=('M' in mytz.upper()))
    
    tz_from = get_timezone(mytz)
    if tz_from is None:
        return None
        
    time = datetime.now(tz_from)

    fmt = "%I:%M %p (UT%z)"
    return time.strftime(fmt)
  
  
def get_lst(longitude):
    """
    Gets the Local Sidereal Time
    
    Args:
        longitude: decimal degrees (west is negative so longitude ranges from [-180,180])
    """  
    t = astropy.time.Time(datetime.utcnow())
    jd0 = (t.jd-0.5) // 1 + 0.5
    ut = ((t.jd-0.5) % 1) * 24
    T=(jd0-2451545.0)/36525.0
    T0 = 6.697374558+ (2400.051336*T)+(0.000025862*T**2)+(ut*1.0027379093)
    GST = T0 % 24
    LST = (GST + longitude/15) % 24
    
    LST_hour = LST//1
    LST_min = (LST % 1) * 60
    LST_sec = round((LST_min % 1) * 60)
    LST_min = LST_min // 1
    LST_str = "%02d:%02d:%02d" % (LST_hour, LST_min, LST_sec)
    return LST_str
    
    
def get_jd(modified=True):
    """
    Gets the JD or MJD
    
    Args:
        modified: if True, get MJD instead
    """
    t = astropy.time.Time(datetime.utcnow())
    jd = t.jd
    if modified:
        jd -= 2400000.5
        
    return "{0:.5f}".format(jd)

# print(get_time_now('PDT'))
# print(get_time_now('CLT'))
# print(convert_time('1:45', 'PDT', 'CLT'))
    
