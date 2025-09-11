# Let's check the current directory structure
import os

print("Current directory:", os.getcwd())
print("\nFiles in current directory:")
for item in os.listdir("."):
    print(f"  {item}")

# Check if there's a Download directory
if os.path.exists("Download"):
    print("\nFiles in Download/:")
    for item in os.listdir("Download"):
        print(f"  {item}")
        
if os.path.exists("Download/exported-assets"):
    print("\nFiles in Download/exported-assets/:")
    for item in os.listdir("Download/exported-assets"):
        print(f"  {item}")