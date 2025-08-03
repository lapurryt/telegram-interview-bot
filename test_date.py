from datetime import datetime

today = datetime.now()
print(f"Today is: {today.strftime('%A, %d.%m.%Y')}")
print(f"Weekday number: {today.weekday()} (0=Monday, 6=Sunday)")

# Test the get_available_dates function
def get_available_dates():
    """Get 5 available weekdays starting from today"""
    available_dates = []
    current_date = datetime.now()
    
    # Start from today
    next_date = current_date
    
    # Find 5 weekdays (Monday to Friday)
    count = 0
    while count < 5:
        if next_date.weekday() < 5:  # Monday = 0, Friday = 4
            available_dates.append(next_date)
            count += 1
        next_date += timedelta(days=1)
    
    return available_dates

from datetime import timedelta
dates = get_available_dates()
print("\nAvailable dates:")
for date in dates:
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    print(f"- {date.strftime('%d.%m')} {day_names[date.weekday()]}") 