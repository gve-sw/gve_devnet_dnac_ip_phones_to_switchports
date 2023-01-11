""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

# Import section
from dnacentersdk import DNACenterAPI, ApiError
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from config import *

import csv, sys
from datetime import date

console = Console()


def main():
    console.print(Panel.fit("DNAC Phone Report Tool"))

    # Get Time stamp for file, create file name
    today = date.today()
    today_string = today.strftime("%m-%d-%Y")

    filename = 'dnac_phones_{}.csv'.format(today_string)

    # Connect to DNAC
    console.print(Panel.fit("Connect to DNAC", title="Step 1"))

    try:
        dna_center = DNACenterAPI(username=DNAC_USERNAME, password=DNAC_PASSWORD, base_url=DNAC_BASE_URL, verify=False,
                                  version="2.3.3.0")
        console.print("DNAC Connection Established!")
    except ApiError as e:
        console.print('[red]Error:[/] unable to connect to DNAC instance: {}'.format(e.details))
        sys.exit(-1)

    console.print(Panel.fit("Get Phone Information", title="Step 2"))

    # Get phones from physical topology (looking for HOST nodes, phones have SEP in their name)
    physical_topology = dna_center.topology.get_physical_topology(node_type="HOST")['response']['nodes']

    phones = []
    for node in physical_topology:
        if 'SEP' in node['label']:
            phones.append(node)

    node_count = len(phones)

    console.print("Found [green]{}[/] phones.".format(node_count))

    # Create DNAC Phone Report File
    with open(filename, 'w') as fp:

        # CSV Headers
        fieldnames = ['Switch', 'Port', 'Phone Mac Address']

        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        with Progress() as progress:
            overall_progress = progress.add_task("Overall Progress", total=node_count, transient=True)
            counter = 1

            # Extract relevant data from each phone, add to csv
            for phone in phones:
                progress.console.print(
                    "Processing: Mac Address - [green]{}[/] ({} of {})".format(phone['additionalInfo']['macAddress'], str(counter), node_count))

                # Get switch and port details
                details = dna_center.clients.get_client_detail(mac_address=phone['additionalInfo']['macAddress'])['detail']

                # Extract relevant information
                phone_data = {
                    'Switch': details['clientConnection'],
                    'Port': details['port'],
                    'Phone Mac Address': details['hostMac']
                }

                # Write to csv file
                writer.writerow(phone_data)

                counter += 1
                progress.update(overall_progress, advance=1)

        console.print("All Phones Processed!")

        console.print("Phone records written to [blue]{}[/]".format(filename))
    return


if __name__ == '__main__':
    main()
