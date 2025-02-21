#!/usr/bin/env python3
"""
CloudTunnel

Author: Obsivium
GitHub: https://github.com/Obsivium
Version: 0.0.3
"""

import os, sys, subprocess, time, json, requests, threading, re


def bind_stdout(process: subprocess.Popen, callback):
    """
    Binds a subprocess instance's stdout to a callback function.
    Whenever stdout updates, the callback function is called with the latest output.
    """

    def read_output():
        for line in iter(process.stdout.readline, ""):  # Reads line-by-line
            callback(line.strip())  # Call the function with new output
        # Run the output reader in a background thread

    thread = threading.Thread(target=read_output, daemon=True)
    thread.start()


def check_requirements():
    """Ensure the script runs only on Linux and has necessary dependencies."""
    if os.name != "posix":
        print("Error: This script is only for Linux.")
        sys.exit(1)

    try:
        import requests
    except ImportError:
        print("Error: 'requests' module is not installed. Install it using:")
        print("    pip install requests")
        sys.exit(1)


def ask_question(questions: list[str], main_question: str) -> int:
    """Prompt user with a multiple-choice question and return their selection."""
    print(main_question)
    for i, question in enumerate(questions):
        print(f"[{i}] {question}")

    while True:
        try:
            answer = int(input("-> "))
            if 0 <= answer < len(questions):
                return answer
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def setup_playit() -> str:
    """Download Playit based on system architecture. Then return the executable name."""
    options = [
        "x86-64 (Most Likely)",
        "i686 (32-bit)",
        "armv7 (Raspberry Pi 1/2)",
        "aarch64 (Raspberry Pi 3/4/5)",
    ]
    executables = ["amd64", "i686", "armv7", "aarch64"]
    base_url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-linux-"

    answer = ask_question(options, "Select your system architecture:")

    file_name = f"playit-linux-{executables[answer]}"
    download_url = base_url + executables[answer]

    if os.path.exists(file_name):
        print(f"✅Playit is already downloaded: {file_name}")
    else:
        subprocess.run(["wget", download_url], check=True)
        subprocess.run(["chmod", "+x", file_name], check=True)

    # get the secret path
    secret_path = (
        subprocess.check_output([f"./{file_name}", "secret-path"]).decode().strip()
    )

    # if there is no file at secret path, warn the user
    while not os.path.exists(secret_path):
        print("❌Warning: No secret file found at the specified path.")
        print("Please login to your playit account.")
        print("Once you are logged in, press CTRL+C to continue.")
        os.system(f"./{file_name}")

    return file_name


def read_credentials() -> dict:
    """Read credentials from credentials.txt file."""
    try:
        with open("credentials.txt", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Invalid or missing 'credentials.txt'. Please set up credentials.")
        sys.exit(1)


def start_playit(playit_executable: str):
    """Start Playit tunnel."""
    print(f"🚀 Starting Playit tunnel using {playit_executable}...")
    try:
        playit_instance = subprocess.Popen(
            [f"./{playit_executable}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Merge stdout and stderr
            text=True,
            shell=True,
        )
    except FileNotFoundError:
        print("❌ Error: Playit executable not found.")
        print("Downloading Playit")
        setup_playit()
    return playit_instance


def update_dns_record(
    zone_id: str, record_id: str, api_token: str, target: str, port: str
):
    """Update Cloudflare DNS SRV record."""
    url = (
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    )
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    data = {"data": {"port": port, "target": target}}

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ DNS record updated successfully!")
    else:
        print(f"❌ Failed to update DNS record: {response.status_code}")
        print(response.text)


def setup_credentials():
    """Prompt the user to enter required credentials and save them."""
    print("Obtain the necessary tokens from this guide:")
    print(
        "https://medium.com/@oliverbravery/publically-exposing-tcp-ports-with-static-url-without-port-forwarding-9ddd32ca2726"
    )

    zone_id = input("Enter Cloudflare Zone ID: ")
    api_token = input("Enter Cloudflare API Token: ")

    print("Fetching available SRV records...")

    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
            headers=headers,
        )
        response.raise_for_status()
        records = response.json()["result"]
    except (requests.RequestException, KeyError):
        print("Error: Failed to fetch SRV records.")
        sys.exit(1)

    srv_records = [r for r in records if r["type"] == "SRV"]
    if not srv_records:
        print("Error: No SRV records found for this domain.")
        sys.exit(1)

    selected_record = srv_records[
        ask_question([r["name"] for r in srv_records], "Select the SRV record to use:")
    ]

    credentials = {
        "CLOUDFLARE_API_TOKEN": api_token,
        "ZONE_ID": zone_id,
        "DNS_RECORD": selected_record,
    }

    with open("credentials.txt", "w") as file:
        json.dump(credentials, file, indent=4)

    print("✅ Credentials saved successfully!")


dns_changed_urls: list = []


def is_a_new_url(command: str) -> list:
    regex = "(.+)=>(.+)"
    if re.search(regex, command):
        exposed_url, local_url = command.split("=>")
        if exposed_url in dns_changed_urls:
            return [None, None]
        dns_changed_urls.append(exposed_url)
        port = local_url.split(":")[-1]
        port = port.split(" ")[0]
        exposed_url = exposed_url.replace(" ", "")
        local_url = local_url.replace(" ", "")
        return [exposed_url, port]
    return [None, None]


def playit_loop(credentials: dict, playit_instance: subprocess.Popen):
    last_command = ""
    while True:
        if playit_instance.stdout is None:
            continue
        if output := playit_instance.stdout.readline():
            exposed_url, port = is_a_new_url(output.strip())
            print(exposed_url, port)
            if exposed_url is None or port is None:
                continue
            print("🚀Updating DNS record...")
            print(output)
            update_dns_record(
                credentials["ZONE_ID"],
                credentials["DNS_RECORD"]["id"],
                credentials["CLOUDFLARE_API_TOKEN"],
                exposed_url,
                port,
            )
    rc = playit_instance.poll()


def main():
    """Main execution flow."""
    check_requirements()

    if "credentials.txt" not in os.listdir():
        setup_credentials()

    playit_file = setup_playit()
    credentials = read_credentials()
    playit_instance = start_playit(playit_executable=playit_file)

    time.sleep(1)

    playit_loop(credentials=credentials, playit_instance=playit_instance)


if __name__ == "__main__":
    main()
