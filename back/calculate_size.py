import os
import sys
import subprocess

# Function to calculate the directory size
def get_dir_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

# Run pip list to get all the installed packages
result = subprocess.run([sys.executable, '-m', 'pip', 'list'], stdout=subprocess.PIPE)
installed_packages = result.stdout.decode('utf-8').split('\n')[2:]  # Skip the header lines

total_size = 0

for package in installed_packages:
    package_name = package.split()[0]

    # For each package, use pip show to find the size and add it to the total
    if package_name:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], stdout=subprocess.PIPE)
        package_details = result.stdout.decode('utf-8').split('\n')
        
        # Find the location of the package
        location = ''
        for detail in package_details:
            if detail.startswith('Location:'):
                location = detail.split(':')[1].strip()
                break
        
        # If location is found, calculate the size of the package
        if location:
            package_dir = os.path.join(location, package_name.replace('-', '_'))
            if os.path.isdir(package_dir):
                size = get_dir_size(package_dir)
                total_size += size
                print(f'{package_name}: {size / (1024 * 1024):.2f} MB')

print(f'Total size of packages: {total_size / (1024 * 1024):.2f} MB')
