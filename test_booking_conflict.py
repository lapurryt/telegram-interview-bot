#!/usr/bin/env python3
"""
Test script to demonstrate booking conflict prevention
"""

from datetime import datetime, timedelta

# Simulate the interview_bookings dictionary
interview_bookings = {}

def get_booked_slots_for_date(selected_date):
    """Get all booked time slots for a specific date"""
    booked_slots = []
    for booking_key, booking_data in interview_bookings.items():
        if booking_data['date'] == selected_date:
            # Extract time slot index from booking key
            try:
                time_slot_index = int(booking_key.split('_')[1])
                booked_slots.append(time_slot_index)
            except (IndexError, ValueError):
                continue
    
    return booked_slots

def is_time_slot_available(selected_date, time_slot_index):
    """Check if a time slot is available for booking"""
    # Check if this specific time slot is already booked
    booking_key = f"{selected_date}_{time_slot_index}"
    
    if booking_key in interview_bookings:
        return False
    
    return True

def simulate_booking(user_id, selected_date, time_slot_index):
    """Simulate a booking"""
    booking_key = f"{selected_date}_{time_slot_index}"
    
    if is_time_slot_available(selected_date, time_slot_index):
        interview_bookings[booking_key] = {
            'user_id': user_id,
            'date': selected_date,
            'time': f"Time slot {time_slot_index}",
            'user_name': f"User {user_id}"
        }
        print(f"✅ User {user_id} successfully booked {selected_date} slot {time_slot_index}")
        return True
    else:
        print(f"❌ User {user_id} cannot book {selected_date} slot {time_slot_index} - ALREADY BOOKED!")
        return False

def show_available_slots(selected_date):
    """Show available and booked slots for a date"""
    booked_slots = get_booked_slots_for_date(selected_date)
    time_slots = [
        "09:00 - 10:00",
        "10:00 - 11:00", 
        "11:00 - 12:00",
        "14:00 - 15:00",
        "15:00 - 16:00",
        "16:00 - 17:00"
    ]
    
    print(f"\n📅 Available slots for {selected_date}:")
    for i, time_slot in enumerate(time_slots):
        if i in booked_slots:
            print(f"❌ {time_slot} (Занято)")
        else:
            print(f"✅ {time_slot}")

def test_booking_conflict():
    """Test the booking conflict prevention system"""
    print("🧪 Testing Booking Conflict Prevention System")
    print("=" * 50)
    
    test_date = "2025-08-04"
    
    # Test 1: First booking should succeed
    print("\n1️⃣ First booking attempt:")
    simulate_booking(1, test_date, 1)  # 10:00 - 11:00
    show_available_slots(test_date)
    
    # Test 2: Second booking of same slot should fail
    print("\n2️⃣ Second booking attempt (same slot):")
    simulate_booking(2, test_date, 1)  # Should fail
    show_available_slots(test_date)
    
    # Test 3: Different slot should succeed
    print("\n3️⃣ Third booking attempt (different slot):")
    simulate_booking(3, test_date, 2)  # 11:00 - 12:00
    show_available_slots(test_date)
    
    # Test 4: Another booking on same date
    print("\n4️⃣ Fourth booking attempt:")
    simulate_booking(4, test_date, 4)  # 14:00 - 15:00
    show_available_slots(test_date)
    
    # Show final state
    print(f"\n📊 Final booking state:")
    for booking_key, booking_data in interview_bookings.items():
        print(f"  - {booking_key}: User {booking_data['user_id']}")

if __name__ == "__main__":
    test_booking_conflict() 