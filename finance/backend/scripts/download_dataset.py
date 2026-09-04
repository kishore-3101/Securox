import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_dataset")

URL = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B_20Percent.txt"

# KDD features header
HEADER = (
    "duration,protocol_type,service,flag,src_bytes,dst_bytes,land,wrong_fragment,"
    "urgent,hot,num_failed_logins,logged_in,num_compromised,root_shell,su_attempted,"
    "num_root,num_file_creations,num_shells,num_access_files,num_outbound_cmds,"
    "is_host_login,is_guest_login,count,srv_count,serror_rate,srv_serror_rate,"
    "rerror_rate,srv_rerror_rate,same_srv_rate,diff_srv_rate,srv_diff_host_rate,"
    "dst_host_count,dst_host_srv_count,dst_host_same_srv_rate,dst_host_diff_srv_rate,"
    "dst_host_same_src_port_rate,dst_host_srv_diff_host_rate,dst_host_serror_rate,"
    "dst_host_srv_serror_rate,dst_host_rerror_rate,dst_host_srv_rerror_rate,"
    "class,difficulty\n"
)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    csv_path = os.path.join(data_dir, "nsl_kdd.csv")
    
    if os.path.exists(csv_path):
        logger.info(f"Dataset already exists at {csv_path}")
        return

    logger.info(f"Downloading NSL-KDD dataset from {URL}...")
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(HEADER)
            f.write(data)
            
        logger.info(f"Dataset downloaded and saved to {csv_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")

if __name__ == "__main__":
    main()
