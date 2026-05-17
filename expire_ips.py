import os
import shutil
from datetime import datetime

CONF_FILE = "/etc/nginx/allowlist.conf"
TEMP_FILE = CONF_FILE + ".tmp"

def manage_allowlist():
    today = datetime.now()
    changed = False
    updated_lines = []

    if not os.path.exists(CONF_FILE):
        print(f"Error: {CONF_FILE} not found.")
        return

    with open(CONF_FILE, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
	    line = lines[i].strip()
	    
	    if not line.startswith("# expire after "):
	        updated_lines.append(lines[i])
	        i += 1
	        continue

	    try:
	        date_str = line.replace("# expire after ", "").strip()
	        expiry_date = datetime.strptime(date_str, "%Y-%m-%d")
	        
	        updated_lines.append(lines[i]) # Keep the comment line
	        i += 1 # Move to the 'allow' line
	        
	        if i < len(lines):
	            next_line = lines[i]
	            # Handle expiration logic
	            if today > expiry_date and not next_line.strip().startswith("#"):
	                updated_lines.append(f"#{next_line}")
	                changed = True
	            else:
	                updated_lines.append(next_line)
	    
	    except ValueError:
	        # If date is invalid, just keep the comment line and let the 
	        # end-of-loop increment handle moving to the next line
	        updated_lines.append(lines[i])

	    # Final increment to move past the 'allow' line (or the invalid line)
	    i += 1

    if changed:
        with open(TEMP_FILE, 'w') as f:
            f.writelines(updated_lines)
        
        shutil.move(TEMP_FILE, CONF_FILE)
        
        exit_code = os.system("nginx -t > /dev/null 2>&1")
        if exit_code == 0:
            os.system("systemctl reload nginx")
            print(f"[{datetime.now()}] Success: Expired IPs commented and Nginx reloaded.")
        else:
            print(f"[{datetime.now()}] Error: Nginx config check failed. Changes not applied.")
    else:
        print(f"[{datetime.now()}] No changes needed.")

if __name__ == "__main__":
    manage_allowlist()
