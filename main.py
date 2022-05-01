import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from multiprocessing import Pool


start_time = time.time()


# Get basic players information for all players
def get_basic_info(offset):
    base_url = "https://sofifa.com/players?offset="
    columns = ['ID', 'Name', 'Age',
               'Nationality', 'Overall', 'Potential',
               'Club', 'Contract', 'Value',
               'Wage', 'Total stat']
    data = pd.DataFrame(columns=columns)

    url = base_url + str(offset * 60)
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    table_body = soup.find('tbody')
    for row in table_body.findAll('tr'):
        td = row.findAll('td')

        pid = td[0].find('img').get('id')
        name = td[1].find('a')['aria-label']
        age = td[2].text
        nationality = td[1].find('img').get('title')

        overall = td[3].text
        potential = td[4].text

        club = td[5].find('a').text
        contract = td[5].find('div', {'class': 'sub'}).text.strip()

        value = td[6].text.strip()
        wage = td[7].text.strip()
        total_stat = td[8].text.strip()

        player_data = pd.DataFrame([[pid, name, age,
                                     nationality, overall, potential,
                                     club, contract, value, wage, total_stat]])
        player_data.columns = columns
        data = pd.concat([data, player_data], axis=0, ignore_index=True)

    return data


# Get detailed player information from player page
def get_details(pid):

    player_data_url = 'https://sofifa.com/player/'
    url = player_data_url + str(pid)

    print(url, time.time()-start_time)

    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    skill_map = {'ID': pid}

    # making sure the player is in fifa 22
    fifa_ver = soup.find('span', {'class': 'bp3-button-text'})
    if fifa_ver.text != "FIFA 22":
        return None

    # real overall rating for each position
    pos = soup.findAll('div', {'class': 'bp3-tag'})
    for att in pos:
        rat = att.get_text(strip=True, separator='\n').splitlines()
        num = rat[1].split('+')
        skill_map[rat[0]] = sum([int(n) for n in num])

    # player info
    meta_data = soup.find('div', {'class': 'meta'}).text.split(' ')

    length = len(meta_data)
    weight = meta_data[length - 1]
    height = meta_data[length - 2]
    skill_map["Height"] = height.split('cm')[0]
    skill_map['Weight'] = weight.split('kg')[0]

    dob = " ".join(meta_data[(length - 5): (length - 2)])[1:-1]
    skill_map['DOB'] = dob

    blocks = soup.findAll('div', {'class': ['block-quarter']})

    profile_blocks = blocks[4].findAll('li')
    skill_map['Preferred foot'] = profile_blocks[0].prettify().split()[-2]
    skill_map['Weak foot'] = profile_blocks[1].prettify().split()[2]
    skill_map['Skill move'] = profile_blocks[2].prettify().split()[2]
    skill_map['International reputation'] = profile_blocks[3].prettify().split()[2]
    skill_map['Work rate'] = "".join(profile_blocks[4].prettify().split()[-4:-2])

    body_type = profile_blocks[5].prettify().split()[-4:-2]
    if '<span>' in body_type:
        skill_map['Body type'] = profile_blocks[5].prettify().split()[-3]
    else:
        skill_map['Body type'] = " ".join(body_type)

    print(profile_blocks[6].prettify().split()[-3])
    skill_map['Real face'] = profile_blocks[6].prettify().split()[-3]
    skill_map['Release clause'] = profile_blocks[7].prettify().split()[-3]

    if len(blocks) == 15:
        skill_block = blocks[7:14]
    else:
        skill_block = blocks[8:15]

    for block in skill_block:
        for li in block.findAll('span'):

            if len(li.text) <= 2:
                skill_val = int(li.text)

            else:
                des = li.text
                try:
                    skill_map[des] = skill_val
                except NameError:
                    skill_map[des] = 'NaN'

    trait_block = blocks[-1]
    traits = ', '.join([span.text for span in trait_block.findAll('span')])

    if traits:
        skill_map['Traits'] = traits
    else:
        skill_map['Traits'] = "None"

    return skill_map


if __name__ == '__main__':
    print('Executing...')

    # # getting the basic info before details
    # with Pool(5) as p:
    #     output = p.map(get_basic_info, [i for i in range(400)])
    #     df = pd.concat([i for i in output], axis=0, ignore_index=True)
    # print(f'Dropping {df.duplicated().values.sum()} duplicates...')
    # df.drop_duplicates(inplace=True)
    # df.to_csv("basic_info.csv")
    #
    # # getting detailed info into another table
    # df = pd.read_csv('basic_info.csv')
    # id_array = df['ID']
    # print(len(id_array))
    # with Pool(20) as p:
    #     output = p.map(get_details, [i for i in id_array])
    #
    #     detailed_df = pd.concat([pd.DataFrame(i, index=[0]) for i in output if i],
    #                             ignore_index=True)
    #
    # detailed_df.to_csv("detailed_info.csv")

    print("Done. Execution time: %s seconds" % (time.time() - start_time))


