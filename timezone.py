from datetime import datetime
import pytz as tz


all_timezones = tz.common_timezones
all_abbreviations = {} # convert from abbreviation to full time zone
for zone in all_timezones:
    abbrev = tz.timezone(zone).localize(datetime.now()).strftime('%Z')
    if abbrev == 'CLT' and 'Santiago' not in zone:
        continue
    all_abbreviations[abbrev] = zone

def get_timezone(tz_abbrev):
    """
    Convert form time zone abbrevaiton (3 characeters) to full time zone
    """
    new_tz_abbrev = tz_abbrev
    # check for daylight savings
    if tz_abbrev.upper()[1] == 'D':
        dst = True
        # check to make sure the lookup is this version
        # else switch abbreviation to standard time
        if not tz_abbrev in all_abbreviations:
            new_tz_abbrev[1] = 'S'
    else:
        dst = False
        # check to make sure the lookup is this version
        # else switch abbreviation to DST time
        if not tz_abbrev in all_abbreviations:
            new_tz_abbrev[1] = 'D'
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
    Get current time in this time zone
    
    Args:
        mytz: abbrevation e.g. CLT
    """
    tz_from = get_timezone(mytz)
    if tz_from is None:
        return None
        
    time = datetime.now(tz_from)

    fmt = "%I:%M %p (UT%z)"
    return time.strftime(fmt)
    

# print(get_time_now('PDT'))
# print(get_time_now('CLT'))
# print(convert_time('1:45', 'PDT', 'CLT'))
    
