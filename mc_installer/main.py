import json
import requests
import os
import argparse
from tqdm import *
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


CURSEFORGE_API_BASE = "https://curseforge.com/api/v1"
SERVER_PACK_BASE = "output/"


def download_forge(dir_path,minecraft_ver,forge_ver):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    download_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{minecraft_ver}-{forge_ver}/forge-{minecraft_ver}-{forge_ver}-installer.jar"

    response = requests.get(download_url,allow_redirects = True)

    file_path = None
    if response.status_code == 200:
        final_url = response.url;        
        filename = final_url.split("/")[-1]

        file_path = os.path.join(dir_path, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return os.path.abspath(file_path)
    else:
        print(f"Failed to download forge from uri {download_url}")
        return None
def install_forge(installer_path,dir_path):
    if not os.path.exists(installer_path):
        print("Forge executable not found")
        return

    command = ["java","-jar",installer_path,"--installServer"]

    subprocess.run(command,cwd=dir_path)


def download_with_browser(project_id,file_id):
    project_uri = f"https://www.curseforge.com/projects/{project_id}"
    # project_response = requests.get(project_uri,allow_redirects = True)
    raise Exception(f"{project_uri} has API access disabled. Please download it manually")

def download_mod(mods_path,project_id, file_id, verbose = False):
    download_url = f"{CURSEFORGE_API_BASE}/mods/{project_id}/files/{file_id}/download"

    if verbose:
        tqdm.write(f"Downloading {download_url}...")

    if not os.path.exists(mods_path):
        os.makedirs(mods_path)

    response = requests.get(download_url,allow_redirects = True)

    if verbose:
        tqdm.write(response)
    
    if(response == None):
        raise Exception(f"Response for {download_url} was None!")
    if(response.status_code == 404):
        response = download_with_browser(project_id,file_id)

    if response.status_code == 200:
        final_url = response.url;        
        filename = final_url.split("/")[-1]

        file_path = os.path.join(mods_path, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    else:
        raise Exception(f"Failed to download file {download_url}: {response.status_code}")
def extract_loader_version(data):
    minecraft_info = data.get("minecraft", {})
    version = minecraft_info.get("version")
    mod_loaders = minecraft_info.get("modLoaders", [])
    
    for mod_loader in mod_loaders:
        if mod_loader.get("primary"):
            mod_loader_id = mod_loader.get("id", "")
            forge_version = mod_loader_id.replace("forge-", "")
            return version, forge_version
    
    return version, None  # Return None if no primary mod loader is found

def main():
    parser = argparse.ArgumentParser(description='Download files referenced in a JSON file.')
    parser.add_argument('manifest_file', type=str, help='Path to the JSON file')


    parser.add_argument('--skip-mods', action='store_true', help='Use to skip the mod download phase')
    parser.add_argument('--skip-forge-install', action='store_true', help='Use to skip the mod download phase')


    parser.add_argument('--verbose', action='store_true', help='Use to skip the mod download phase')
    
    args = parser.parse_args()

    
    json_filename = args.manifest_file
    skip_mods = args.skip_mods
    skip_forge_install = args.skip_forge_install

    verbose = args.verbose


    
    try:
        data = None
        with open(json_filename, 'r') as file:
            data = json.load(file)
        
    except FileNotFoundError:
        print(f"File not found: {json_filename}")
        return
    except json.JSONDecodeError:
        print("Error decoding JSON file.")
        return


    game_version,loader_version = extract_loader_version(data)


    output_dir = data.get('name')+data.get('version')

    forge_path = download_forge(output_dir,minecraft_ver = game_version,forge_ver = loader_version)

    if forge_path != None:
        print(f"Forge downloaded to {forge_path}")

        if not skip_forge_install:
            print("Installing forge...")
            install_forge(forge_path,output_dir)
        
    

    
    files = data.get('files', [])

    
    
    if not skip_mods:
        # Use ThreadPoolExecutor to download files concurrently
        errors = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for file_info in files:
                project_id = file_info.get('projectID')
                file_id = file_info.get('fileID')
                if project_id and file_id:
                    futures.append(executor.submit(download_mod, f"{output_dir}/mods/", project_id, file_id, verbose))
                else:
                    print(f"Invalid file information: {file_info}")

            for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading mods..."):
                try:
                    future.result()  # Wait for all futures to complete
                except Exception as e:
                    errors.append(e)
        if len(errors) > 0:
            print("Errors while downloading:")
            for error in errors:
                print(error)
                    
if __name__ == "__main__":
    main()
