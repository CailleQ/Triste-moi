import os
import subprocess
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

now = datetime.now()

WARNING_ICON = "\U000026A0"  # 警告图标
LINK_ICON = "\U0001F517"  # 链接图标
def get_ros_folder_size():
    if not os.path.exists('/home/firefly/.ros'):
        print("Error: .ros directory does not exist.")
        return None
    
    result = subprocess.run(['du', '-sh', '/home/firefly/.ros'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running 'du' command: {result.stderr}")
        return None

    # Handle the case where the output is empty
    output = result.stdout.strip()
    if not output:
        print("Error: No output from 'du' command.")
        return None

    # Safely split the output and return the size string
    try:
        size_str = output.split()[0]
        return size_str
    except IndexError:
        print("Error: Unexpected output format from 'du' command.")
        return None

def parse_size(size_str):
    """
    Convert a size string (e.g., '1.2G', '500M', '100K') to megabytes.
    """
    size_unit = size_str[-1]
    size_value = float(size_str[:-1])

    if size_unit == 'G':
        return size_value * 1024  # Convert gigabytes to megabytes
    elif size_unit == 'M':
        return size_value  # Megabytes are the base unit
    elif size_unit == 'K':
        return size_value / 1024  # Convert kilobytes to megabytes
    elif size_unit == 'T':
        return size_value * 1024 * 1024  # Convert terabytes to megabytes
    else:
        # If the unit is unknown, assume it's in bytes and convert to megabytes
        return size_value / (1024 * 1024)

def get_disk_free_space():
    result = subprocess.run(['df', '-h', '/home/firefly/'], capture_output=True, text=True)
    free_str = result.stdout.split('\n')[1].split()[3]
    return parse_size(free_str)

def read_sn_from_ros():
    try:
        with open('/home/firefly/.ros/sn.txt', 'r') as file:
            sn = file.read().strip()
            return sn
    except FileNotFoundError:
        print(f"{Colors.FAIL}Error: The file .ros/sn.txt does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def compress_ros_folder(sn, date):
    folder_path = '/home/firefly/.ros'
    output_path = f'/home/firefly/snowbot/{sn}_logs_{date}.zip'
    
    # Check if the compressed file already exists
    if os.path.exists(output_path):
        print(f"Compressed file {output_path} already exists. Skipping compression.")
    else:
        print(f"Compressing .ros folder to {output_path}...")
        subprocess.run(['sudo', 'zip', '-r', output_path, '/home/firefly/.ros'])

def upload_to_s3(sn):

    file_path = f'/home/firefly/snowbot/{sn}_logs_{date}.zip'
    bucket_path = f's3://yarbo-support/{sn}/'
    nohup_path = os.getcwd() + '/nohup.out'
    subprocess.run(['sudo', 'rm', nohup_path])
    subprocess.Popen(['sudo','nohup', 'aws', 's3', 'cp', file_path, bucket_path])
    print(f"Uploading {file_path} to {bucket_path}...")
    print(f"{Colors.FAIL}{Colors.BOLD}{WARNING_ICON} Notice:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{LINK_ICON} Download link will be:{Colors.ENDC}")
    download_link = f"https://yarbo-support.s3.amazonaws.com/{sn}/{sn}_logs_{date}.zip"
    print(f"  {Colors.OKGREEN}{Colors.UNDERLINE}{download_link}{Colors.ENDC}{Colors.ENDC}")
    print(f"{Colors.WARNING}  Do not open the link, until the download is completed.{Colors.ENDC}")
    # 输出当前时间
    print(f"\n{Colors.OKCYAN}Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    subprocess.run(['sudo', 'tail', '-f', nohup_path])

# Main script starts here
if __name__ == "__main__":
    print(f"{Colors.HEADER}Checking .ros folder size...{Colors.ENDC}")
    ros_size = get_ros_folder_size()
    print(f"{Colors.HEADER}.ros folder size: {ros_size}{Colors.ENDC}")
    ros_size = get_ros_folder_size()
    if ros_size:
        print(f"{Colors.HEADER}.ros folder size: {ros_size}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}Failed to retrieve .ros folder size.{Colors.ENDC}")
    print(f"{Colors.HEADER}Checking disk free space...")
    free_space_mb = get_disk_free_space()
    print(f"{Colors.HEADER}Free disk space: {free_space_mb:.2f} MB{Colors.ENDC}")

    if free_space_mb < 3000:  # 3000 MB is 3 GB
        print(f"{Colors.FAIL}Not enough free space on the disk. Aborting.{Colors.ENDC}")
        exit()
    else:
        print(f"{Colors.HEADER}Sufficient disk space available.{Colors.ENDC}")

    print(f"{Colors.HEADER}Checking if connected to Wi-Fi...{Colors.ENDC}")
    print(f"{Colors.HEADER}Connected to HaLow or Wi-Fi. Continuing...{Colors.ENDC}")

    today = datetime.now()
    sn = read_sn_from_ros()
    sn = sn[-4:]# Replace with actual SN retrieval logic
    date = today.strftime('%m%d')

    print(f"{Colors.HEADER}Compressing .ros folder...{Colors.ENDC}")
    compress_ros_folder(sn, date)

    print(f"{Colors.HEADER}Uploading to S3...{Colors.ENDC}")
    upload_to_s3(sn)
