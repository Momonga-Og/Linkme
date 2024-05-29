import json

# Load cookies from a JSON file
with open('instagram_cookies.json', 'r') as f:
    cookies = json.load(f)

# Open the output file in write mode
with open('instagram_cookies.txt', 'w') as f:
    # Write the Netscape format header
    f.write("# Netscape HTTP Cookie File\n")
    f.write("# This is a generated file! Do not edit.\n\n")

    # Iterate through the JSON cookies and convert them
    for cookie in cookies:
        f.write("\t".join([
            cookie.get("domain", ""),
            "TRUE" if not cookie.get("hostOnly", False) else "FALSE",
            cookie.get("path", ""),
            "TRUE" if cookie.get("secure", False) else "FALSE",
            str(int(cookie.get("expirationDate", 0))),
            cookie.get("name", ""),
            cookie.get("value", "")
        ]) + "\n")
