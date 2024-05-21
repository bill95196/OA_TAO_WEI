import pandas as pd
import holidays
import pytz

def get_nerc_holidays(start_date, end_date, tz=None):
    # Format start_date and end_date to datetime
    start_date = pd.to_datetime(start_date).tz_localize(tz)
    end_date = pd.to_datetime(end_date).tz_localize(tz)

    # Create an object for U.S. public holidays
    us_holidays = holidays.US(years=range(start_date.year, end_date.year + 1))

    # Define NERC holidays based on fixed and observed holidays
    nerc_holiday_names = {
        "New Year's Day",
        "Memorial Day",
        "Independence Day",
        "Labor Day",
        "Thanksgiving",
        "Christmas Day"
    }

    adjusted_holidays = {}
    # Adjust holidays that fall on Sunday to the next day e.g #2023 New York Day on 2023/1/2; 2022 Chrismas on 12/26/2022
    for date, name in us_holidays.items():
        if name in nerc_holiday_names:
            current_date = pd.Timestamp(date)
            # Check if the holiday falls on a Sunday
            if current_date.weekday() == 6:  # Sunday
                # Shift to the next day (Monday)
                observed_date = current_date + pd.Timedelta(days=1)
                adjusted_holidays[observed_date] = name
            else:
                adjusted_holidays[current_date] = name

    # Filter out the holidays within the given date range
    holiday_dates = [
        pd.Timestamp(date).tz_localize(None).tz_localize(tz) for date, name in adjusted_holidays.items()
        if name in nerc_holiday_names
    ]
    holiday_dates = [
        date for date in holiday_dates if date >= start_date and date <= end_date
    ]

    return pd.DatetimeIndex(holiday_dates)





def get_hours(iso, peak_type, period):
  
    if '-' in period:
        # Daily format(e.g."2018-02-03")
        start_date = pd.to_datetime(period)
        end_date = start_date
    elif 'Q' in period:
        # Quarterly format(e.g., "2018Q2")
        start_date = pd.Period(period, freq='Q').start_time
        end_date = pd.Period(period, freq='Q').end_time
    elif len(period) == 7:
        # Monthly format(e.g., "2018Mar")
        start_date = pd.to_datetime(period, format='%Y%b')
        end_date = start_date + pd.offsets.MonthEnd(1)
    elif period.endswith('A'):
        # Annually format(e.g., "2018A")
        year = pd.to_datetime(period[:-1] + '-01-01')
        start_date = year
        end_date = start_date + pd.offsets.YearEnd(1)

    # Generate range of dates depend on different iso
    if  iso.upper() == 'PJM' or iso == 'NYISO': # PJM and NYISO use US Eastern Time year round
        all_dates = pd.date_range(start=start_date, end=end_date + pd.Timedelta(days=1), freq='H',tz = pytz.timezone('US/Eastern'))
        holidays = get_nerc_holidays(start_date, end_date, tz='US/Eastern')
  
    elif iso.upper() == 'SPP' or iso.upper() == 'ERCOT': #SPP and ERCOT use US Central Standard
        all_dates = pd.date_range(start=start_date, end=end_date + pd.Timedelta(days=1), freq='H',tz=pytz.timezone('US/Central'))
        holidays = get_nerc_holidays(start_date, end_date, tz='US/Central')
        
        
    elif iso.upper() ==  'CAISO' or iso.upper() == 'WECC':
        all_dates = pd.date_range(start=start_date, end=end_date + pd.Timedelta(days=1), freq='H',tz=pytz.timezone('US/Pacific'))
        holidays = get_nerc_holidays(start_date, end_date, tz='US/Pacific')
        
    elif iso.upper() == 'MISO': # MISO does not have the daylight-saving setting
        all_dates = pd.date_range(start=start_date, end=end_date + pd.Timedelta(days=1), freq='H')
        holidays = get_nerc_holidays(start_date, end_date)

    
    if 'Q' in period:
        all_dates = all_dates[:-24]
    else:
        all_dates = all_dates[:-1]



    if peak_type.lower() == "onpeak":   # non-NERC holiday weekday from HE7 to HE22
        if iso.upper() ==  'CAISO' or iso.upper() == 'WECC': 
            # Heavy load for CAISO and WECCHE7 to HE22 from Monday to Saturday
            peakdays = all_dates[(all_dates.weekday < 6)  & ~(all_dates.normalize().isin(holidays))] 

        else:  # HE7 to HE22 from Monday to Friday
            peakdays = all_dates[(all_dates.weekday < 5)  & ~(all_dates.normalize().isin(holidays))]  
        valid_hours = range(6, 22)     # (HE7 to HE22) 
        valid_dates = peakdays[peakdays.hour.isin(valid_hours)]
   
    elif peak_type.lower() == "flat": # HE1 to HE24 every day
        valid_dates = all_dates
        
    elif peak_type.lower() == "offpeak":   # flat hour - peak hour
        if iso.upper() ==  'CAISO' or iso.upper() == 'WECC':
            peakdays = all_dates[(all_dates.weekday < 6)  & ~(all_dates.normalize().isin(holidays))] 

        else:
            peakdays = all_dates[(all_dates.weekday < 5)  & ~(all_dates.normalize().isin(holidays))]  
        peak_dates = peakdays[peakdays.hour.isin(range(6, 22))]
        valid_dates = all_dates[~(all_dates.isin(peak_dates))]
        
        
    elif peak_type.lower() == "2x16h":    # HE7 to HE22 for the weekend and the NERC holiday
        
        valid_days = all_dates[(all_dates.weekday >= 5) | (all_dates.normalize().isin(holidays))]  # weekend and holidays
        valid_hours = range(6, 22)
        valid_dates = valid_days[valid_days.hour.isin(valid_hours)]
   
    elif peak_type.lower() == "1x16h":    # CAISO and WECC has 1x16H instead  
        valid_days = all_dates[(all_dates.weekday > 5) | (all_dates.normalize().isin(holidays))]
        valid_hours = range(6, 22)
        valid_dates = valid_days[valid_days.hour.isin(valid_hours)]
        
    
    elif peak_type.lower() == "7x8":   # Non HE7 to HE22 through the week
        valid_days = all_dates
        valid_hours = list(range(0, 6)) + [22, 23]
        valid_dates = valid_days[valid_days.hour.isin(valid_hours)]
        
    
    # Count the valid hours
    num_hours = len(valid_dates)
    
    res = {
        'iso': iso.upper(),
        'peak_type': peak_type.upper(),
        'startdate': start_date.strftime('%Y-%m-%d'),
        'enddate': end_date.strftime('%Y-%m-%d'),
        'num_hours': num_hours
    }
    return res
    
    
    
    
if __name__ == '__main__':
    
    # iso is one of PJM, MISO, ERCOT, SPP, NYISO, WECC and CAISO
    # peak_type is one of onpeak/offpeak/flat/2x16H/7x8 (1x16H for CAISO and WECC)

    iso = 'CAISO'
    peak_type_list = ['onpeak','offpeak']
      
    for i in peak_type_list:
        res = get_hours(iso, i, '2023Nov')
        print(res)
   
