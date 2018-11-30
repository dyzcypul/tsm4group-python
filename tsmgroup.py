"""
Small script to automatically request, parse wowdb data and save as TSM4 groups.
Modify, improve, and distribute as you see fit. Probably contains plenty of bugs.

!Use at your own risk!

***
IMPORTANT: NOT YET FINISHED. OUTPUT WILL INCLUDE SOME CRAFTED ITEMS AND DARKMOON TRINKETS.

Not all crafted items are currently categorized as crafted on wowdb. These may end up in the import string created by this script. If you then import with the option "Move already grouped items?" enabled, these items will be moved from your profession groups to these.
***

Version 1.1:
* Cleaned up the code massively, now utilizing BeautifulSoup to parse the tables and Pandas to handle the data.
* Handles Darkmoon Trinkets now (by excluding Source == 'Created')

-torack on 01.08.2018
"""


import urllib.request

import pandas
from bs4 import BeautifulSoup


def filter_generator(slot_filters, expansion_filters, source_filters):
    """ Generator to iterate over all slot, quality combinations. """
    for expansion_filter in expansion_filters:
        for source_filter in source_filters:
            for slot_filter in slot_filters:
                yield (expansion_filter, expansion_filters[expansion_filter]), (source_filter, source_filter[source_filters]), (slot_filter, slot_filters[slot_filter])


def construct_wowdb_url(xpac_filt, slot_filt, sour_filt, itype='armor', bind=2, craft=-2):
    """ Construct wowdb-url for given filter settings. """
    url = f"https://www.wowdb.com/items/{itype}?filter-bind={bind}&filter-expansion={xpac_filt}&filter-slot={slot_filt}"
    return url


def read_source_from_url(url):
    """ Read URL and return source_code as decoded str. """
    response = urllib.request.urlopen(url)
    return response.read().decode()


def label_item_id(row):
    """ Extract Item_ID from wowdb item url. """
    return int(row['URL'].split('/')[-1].split('-')[0])


def read_item_table_from_wowdb_url(search_html, expansion):
    """ Read and reformat wowdb table returned by url-search. Returns pandas.DataFrame() """
    soup = BeautifulSoup(search_html, 'lxml')
    parsed_table = soup.find_all('table')[1]
    data = [
        [td.a['href'] if td.find('a') else
         ''.join(td.stripped_strings)
         for td in row.find_all('td')]
        for row in parsed_table.find_all('tr')
    ]

    df = pandas.DataFrame(data[1:], columns=[
                          'URL', 'URL2', 'URL3', 'Item Level', 'Req. Level', 'Slot', 'Source', 'Type'])
    if not df.empty:
        df['Item_ID'] = df.apply(lambda row: label_item_id(row), axis=1)
        df['Expansion'] = expansion
        df = df.dropna(axis=0, how='any')[
            ['Item_ID', 'Item Level', 'Req. Level', 'Expansion', 'Slot', 'Source', 'Type']]
    return df


def save_df_as_tsm_groups(df_main, outfile='armor_groups.dat'):
    # tsm_group_sorting: quality -> armour_type -> slot
    expansions = ['PrePanda', 'MoP', 'WoD', 'Legion', 'BFA']
    armor_types = ['Plate', 'Mail', 'Leather',
                   'Cloth', 'Finger', 'Trinket', 'Back', 'Neck']
    slots = ['Chest', 'Feet', 'Hands', 'Head',
             'Legs', 'Shoulders', 'Waist', 'Wrists']
    slot_types_as_subgroups = ['Finger', 'Trinket', 'Back', 'Neck']

    title = 'Vendor Items'
    out_str = ''
    for expansion in expansions:
        for armor_type in armor_types:
            if armor_type in slot_types_as_subgroups:
                # get items with those attributes
                df_items = df_main.loc[
                    (df_main['Expansion'] == expansion) &
                    (df_main['Type'] == armor_type)
                ]

                if not df_items.empty:
                    # handle Back, Finger, Trinket group names
                    armor_type_tmp = armor_type
                    if armor_type == 'Back':
                        armor_type_tmp = 'Cloaks'
                    if armor_type == 'Finger':
                        armor_type_tmp = 'Rings'
                    if armor_type == 'Trinket':
                        armor_type_tmp = 'Trinkets'

                    # construct group identifier only if items found
                    out_str += f'group:{title}`{expansion}`{armor_type_tmp},'

                    item_ids = df_items['Item_ID'].values
                    for item_id in item_ids:
                        out_str += f'i:{item_id},'
            else:
                for slot in slots:
                    # select corresponding items from dataframe
                    df_items = df_main.loc[
                        (df_main['Expansion'] == expansion) &
                        (df_main['Type'] == armor_type) &
                        (df_main['Slot'] == slot)
                    ]

                    if not df_items.empty:
                        # construct group identifier
                        out_str += f'group:{title}`{expansion}`{armor_type}`{slot},'

                        item_ids = df_items['Item_ID'].values
                        for item_id in item_ids:
                            out_str += f'i:{item_id},'

    with open(outfile, 'w') as f:
        f.writelines(out_str)


# wowdb filter values per item slot
armor_slot_filters = {
    'Back': 65536,
    'Chest': 32,
    'Feet': 256,
    'Finger': 2048,
    'Hands': 1024,
    'Head': 2,
    'Legs': 128,
    'Neck': 4,  # not needed, Heart of Azeroth
    'Shoulders': 8,
    'Trinket': 4096,
    'Waist': 64,
    'Wrists': 512,
}

weapon_slot_filters = {
    'MainHand': 2097152,
    'OffHand': 16384,
    'OneHand': 8192,
    'Ranged': 32768,
    'TwoHand': 131072
}

expansion_filters = {
    'PrePanda': 4,
    'MoP': 5,
    'WoD': 6,
    'Legion': 7,
    'BFA': 8
}

# wowdb filter values per item quality
quality_filters = {
    'Epic': 16,
    # 'Rare': 8,  # not needed, currently only crafted Rares
    'Uncommon': 4,
}

if __name__ == '__main__':
    df_main = pandas.DataFrame(
        columns=['Item_ID', 'Item Level', 'Req. Level', 'Quality', 'Slot', 'Source', 'Type'])
    for (quality, qual_filt), (slot, slot_filt) in filter_generator(slot_filters, quality_filters):
        search_url = construct_wowdb_url(qual_filt, slot_filt)
        return_html = read_source_from_url(search_url)
        df = read_item_table_from_wowdb_url(return_html, quality)

        if not df.empty:
            # Remove Darkmoon Trinkets, the only items with Source == 'Created'
            df = df[df.Source != 'Created']

            df_main = df_main.append(df)

    df_main = df_main.reset_index(drop=True)
    save_df_as_tsm_groups(df_main, outfile='armor_groups.dat')
