# check_mic_level.py
import speech_recognition as sr
import time

r = sr.Recognizer()
r.dynamic_energy_threshold = False # Turn off auto-adjustment for this test

print("Starting microphone level check...")
print("Please be quiet for 5 seconds to measure ambient noise.")

with sr.Microphone() as source:
    # First, measure the quiet background noise
    r.adjust_for_ambient_noise(source, duration=5)
    print(f"\nFinished measuring ambient noise.")
    print(f"==> AMBIENT NOISE LEVEL is around: {r.energy_threshold:.2f}\n")
    
    print("Now, please speak a few sentences in a normal voice.")
    print("Watch the 'Current Energy' numbers when you speak.")
    print("--------------------------------------------------")
    
    # Now, listen and print the energy level continuously
    while True:
        try:
            print(f"Current Energy: {source.energy_threshold:.2f}")
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nExiting level check.")
            break
        except Exception as e:
            print(e)
            break