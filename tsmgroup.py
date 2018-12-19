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

import json
import time
import urllib.request

import pandas
from bs4 import BeautifulSoup


def filter_generator(expansions, cats):
    """ Generator to iterate over all slot, quality combinations. """
    for expansion in expansions:
        for cat in cats:
            for slot in item_slots[cat]:
                yield (expansion, expansions[expansion]), (cat, cats[cat]), (slot, item_slots[cat][slot])


def construct_wowdb_url(itype, slot, expansion, source):
    """ Construct wowdb-url for given filter settings. """
    #url = f"https://www.wowdb.com/items/{itype}?filter-bind={bind}&filter-expansion={xpac_filt}&filter-slot={slot_filt}&filter-source={sour_filt}"
    url = f"https://www.wowhead.com/{itype}"
    if itype == "armor" or itype == "weapons":
        url += f'/slot:{slot}'
    if itype == "consumable-items" or itype == "trade-goods" or itype == "gems":
        url += f'/live-only:on?filter=166:3:92:128:161;{expansion}:0:1:{source}:1;0:0:0:0:0'
    if itype == "recipe-items":
        url += f'/live-only:on?filter=166:2:92:128:168;{expansion}:2:1:{source}:1;0:0:0:0:0'
    if itype == "miscellaneous-items":
        url += f'/live-only:on?filter=166:2:92:128:168:4;{expansion}:2:1:{source}:1:2;0:0:0:0:0'
    else:
        url += f'/live-only:on?filter=166:3:92:128:161;{expansion}:1:1:{source}:1;0:0:0:0:0'
    print(url)
    return url


def read_source_from_url(url):
    """ Read URL and return source_code as decoded str. """
    response = urllib.request.urlopen(url)
    return response.read().decode()


def label_item_id(row):
    """ Extract Item_ID from wowdb item url. """
    return int(row['URL'].split('/')[-1].split('-')[0])


def read_item_table_from_wowdb_url(search_html, xpac):
    """ Read and reformat wowdb table returned by url-search. Returns pandas.DataFrame() """
    soup = BeautifulSoup(search_html, 'html.parser')
    #parsed_table = soup.find_all('table')[1]
    try:
        parsed_table = soup.find_all('script', type="text/javascript")[1]
    except:
        return pandas.DataFrame(
            columns=['classs', 'id', 'name', 'slot', 'source', 'subclass', 'expansion'])
    output = str(parsed_table).partition(
        'var listviewitems = [{')[2].rpartition('}];')[0]
    output = output.replace("firstseenpatch", "\"firstseenpatch\"")
    output = output.replace("cost", "\"cost\"")
    data = json.loads('[{%s}]' % (output))

    # print(data)

    df = pandas.DataFrame(data, columns=[
                          'classs', 'id', 'name', 'slot', 'source', 'subclass', 'expansion'])

    if not df.empty:
        df['expansion'] = xpac

    return df
    # data = [
    #     [td.a['href'] if td.find('a') else
    #      ''.join(td.stripped_strings)
    #      for td in row.find_all('td')]
    #     for row in parsed_table.find_all('tr')
    # ]

    # df = pandas.DataFrame(data[1:], columns=[
    #                       'URL', 'URL2', 'URL3', 'Item Level', 'Req. Level', 'Slot', 'Source', 'Type'])
    # if not df.empty:
    #     df['Item_ID'] = df.apply(lambda row: label_item_id(row), axis=1)
    #     df['Expansion'] = expansion
    #     df = df.dropna(axis=0, how='any')[
    #         ['Item_ID', 'Item Level', 'Req. Level', 'Expansion', 'Slot', 'Source', 'Type']]
    # return df


def save_df_as_tsm_groups(df_main, outfile, source, cat):
    # tsm_group_sorting: quality -> armour_type -> slot
    #expansions = ['PrePanda', 'MoP', 'WoD', 'Legion', 'BFA']
    #expansions = ['PreBC']
    # armor_types = ['Plate', 'Mail', 'Leather',
    #               'Cloth', 'Finger', 'Trinket', 'Back', 'Neck', 'Shirt', 'Tabard']
    #armor_types = ['Shirt']
    # slots = ['Chest', 'Feet', 'Hands', 'Head',
    #         'Legs', 'Shoulders', 'Waist', 'Wrists']
    slot_types_as_subgroups = ['Finger', 'Trinket', 'Back',
                               'Neck', 'Shirt', 'Tabard', 'Off-hand', 'Shield', 'One-Hand']

    title = f'{source} Items'
    out_str = ''
    for expansion in expansions:
        for slot in item_slots[cat]:
            df_main = df_main.astype({"subclass": str})
            # get items with those attributes
            df_items = df_main.loc[
                (df_main['expansion'] == expansions[expansion]) & 
                (df_main['slot'] == item_slots[cat][slot])
            ]
            df_items = df_items.astype({"id": int})

            if not df_items.empty:
                # handle Back, Finger, Trinket group names
                # construct group identifier only if items found
                subclass = df_items['subclass'].unique()
                for sub in subclass:
                    df = df_items.loc[
                        (df_items['subclass'] == sub)
                    ]
                    if slot not in slot_types_as_subgroups and cat == 'Armor':
                        out_str += f'group:{title}`{expansion}`{cat}`{item_types[cat][sub]}`{slot},'
                    else:
                        if cat == 'Weapons':
                            out_str += f'group:{title}`{expansion}`{cat}`{slot}`{item_types[cat][sub]},'
                        else:
                            print(f"Expansion: {expansion} - Category: {cat} - Subclass: {sub}")
                            out_str += f'group:{title}`{expansion}`{cat}`{item_types[cat][sub]},'
                    item_ids = df['id'].values
                    for item_id in item_ids:
                        out_str += f'i:{item_id},'
        # if cat == 'Armor':
        #     for slot in armor_slots:
        #         df_main = df_main.astype({"subclass": str})
        #         # get items with those attributes
        #         df_items = df_main.loc[
        #             (df_main['expansion'] == expansions[expansion]) &
        #             (df_main['slot'] == armor_slots[slot])
        #         ]
        #         df_items = df_items.astype({"id": int})

        #         # print(df_items)

        #         if not df_items.empty:
        #             # handle Back, Finger, Trinket group names

        #             # construct group identifier only if items found
        #             subclass = df_items['subclass'].unique()
        #             for sub in subclass:
        #                 if slot in slot_types_as_subgroups:
        #                     out_str += f'group:{title}`{expansion}`{cat}`{armor_types[sub]},'
        #                 else:
        #                     out_str += f'group:{title}`{expansion}`{cat}`{armor_types[sub]}`{slot},'
        #                 item_ids = df_items['id'].values
        #                 for item_id in item_ids:
        #                     out_str += f'i:{item_id},'
        # if cat == 'Weapons':
        #     for slot in weapon_slots:
        #         df_main = df_main.astype({"subclass": str})
        #         # get items with those attributes
        #         df_items = df_main.loc[
        #             (df_main['expansion'] == expansions[expansion]) &
        #             (df_main['slot'] == weapon_slots[slot])
        #         ]
        #         df_items = df_items.astype({"id": int})

        #         # print(df_items)

        #         if not df_items.empty:
        #             # handle Back, Finger, Trinket group names

        #             # construct group identifier only if items found
        #             subclass = df_items['subclass'].unique()
        #             for sub in subclass:
        #                 out_str += f'group:{title}`{expansion}`{cat}`{slot}`{weapon_types[sub]},'
        #                 item_ids = df_items['id'].values
        #                 for item_id in item_ids:
        #                     out_str += f'i:{item_id},'
        # if cat == 'Containers':
        #     for slot in container_slots:
        #         df_main = df_main.astype({"subclass": str})
        #         # select corresponding items from dataframe
        #         df_items = df_main.loc[
        #             (df_main['expansion'] == expansions[expansion]) &
        #             (df_main['slot'] == container_slots[slot])
        #         ]
        #         df_items = df_items.astype({"id": int})

        #         # print(df_items)

        #         if not df_items.empty:
        #             # construct group identifier only if items found
        #             subclass = df_items['subclass'].unique()
        #             for sub in subclass:
        #                 out_str += f'group:{title}`{expansion}`{cat}`{container_types[sub]},'
        #                 item_ids = df_items['id'].values
        #                 for item_id in item_ids:
        #                     out_str += f'i:{item_id},'
        # if cat == 'Consumabkes':
        #     for slot in consumable_slots:
        #         df_main = df_main.astype({"subclass": str})
        #         # select corresponding items from dataframe
        #         df_items = df_main.loc[
        #             (df_main['expansion'] == expansions[expansion]) &
        #             (df_main['slot'] == consumable_slots[slot])
        #         ]
        #         df_items = df_items.astype({"id": int})

        #         # print(df_items)

        #         if not df_items.empty:
        #             # construct group identifier only if items found
        #             subclass = df_items['subclass'].unique()
        #             for sub in subclass:
        #                 out_str += f'group:{title}`{expansion}`{cat}`{consumable_types[sub]},'
        #                 item_ids = df_items['id'].values
        #                 for item_id in item_ids:
        #                     out_str += f'i:{item_id},'

    with open(outfile, 'w') as f:
        f.writelines(out_str)


# wowdb filter values per item slot
item_cats = {
    'Weapons': 'weapons',
    'Armor': 'armor',
    'Containers': 'containers',
    'Consumables': 'consumable-items',
    'Trade Goods': 'trade-goods',
    'Recipes': 'recipe-items',
    'Gems': 'gems',
    'Miscellaneous': 'miscellaneous-items'
}

item_slots = {
    'Weapons': {
        'Main Hand': 21,
        'Off Hand': 22,
        'One-Hand': 13,
        'Ranged': 15,
        'Thrown': 25,
        'Two-Hand': 17
    },
    'Armor': {
        'Back': 16,
        'Chest': 5,
        'Feet': 8,
        'Finger': 11,
        'Hands': 10,
        'Head': 1,
        'Off-hand': 23,
        'Legs': 7,
        'Neck': 2,
        'Shield': 14,
        'Shirt': 4,
        'Shoulder': 3,
        'Tabard': 19,
        'Trinket': 12,
        'Waist': 6,
        'Wrist': 9
    },
    'Containers': {
        'Bag': 18
    },
    'Consumables': {
        'Consumable': 0
    },
    'Trade Goods': {
        'Trade Goods': 0
    },
    'Recipes': {
        'Recipe': 0
    },
    'Gems': {
        'Gem': 0
    },
    'Miscellaneous': {
        'Miscellaneous': 0
    }
}

item_types = {
    'Weapons': {
        '15': 'Daggers',
        '13': 'Fist Weapons',
        '0': 'One-Handed Axes',
        '4': 'One-Handed Maces',
        '7': 'One-Handed Swords',
        '6': 'Polearms',
        '10': 'Staves',
        '1': 'Two-Handed Axes',
        '5': 'Two-Handed Maces',
        '8': 'Two-Handed Swords',
        '9': 'Warglaives',
        '2': 'Bows',
        '18': 'Crossbows',
        '3': 'Guns',
        '16': 'Thrown',
        '19': 'Wands',
        '20': 'Fishing Poles',
        '14': 'Misc'
    },
    'Armor': {
        '1': "Cloth",
        '2': 'Leather',
        '3': 'Mail',
        '4': 'Plate',
        '5': 'Cosmetic',
        '-3': 'Amulets',
        '-6': 'Cloaks',
        '8': 'Idols',
        '7': 'Librams',
        '-5': 'Off-hand Frills',
        '11': 'Relics',
        '-2': 'Finger',
        '-7': 'Tabards',
        '-4': 'Trinkets',
        '6': 'Shields',
        '-8': 'Shirts',
        '9': 'Totems',
        '10': 'Sigils',
        '0': 'Misc'
    },
    'Containers': {
        '0': 'Bags',
        '1': 'Soul Bags',
        '2': 'Herb Bags',
        '3': 'Enchanting Bags',
        '4': 'Engineering Bags',
        '5': 'Gem Bags',
        '6': 'Mining Bags',
        '7': 'Leatherworking Bags',
        '8': 'Inscription Bags',
        '9': 'Tackle Boxes',
        '10': 'Cooking Bags'
    },
    'Consumables': {
        '0': 'Consuambles',
        '1': 'Potions',
        '2': 'Elixirs',
        '3': 'Flasks',
        '4': 'Scrolls',
        '5': 'Food & Drinks',
        '6': 'Permanent Item Enhancements',
        '7': 'Bandages',
        '8': 'Other Consumables',
        '9': 'Other Consumables',
        '-3': 'Temporary Item Enchacements'
    },
    'Trade Goods': {
        '0': 'Other',
        '1': 'Parts',
        '2': 'Explosives',
        '3': 'Devices',
        '4': 'Jewelcrafting',
        '5': 'Cloth',
        '6': 'Leather',
        '7': 'Metal & Stone',
        '8': 'Meat',
        '9': 'Herbs',
        '10': 'Elemental',
        '11': 'Other',
        '12': 'Enchanting',
        '13': 'Materials',
        '14': 'Armor Enchantments',
        '15': 'Weapon Enchantments',
        '16': 'Other',
        '-3': 'Other'
    },
    'Recipes': {
        '0': 'Books',
        '1': 'Leatherworking Patterns',
        '2': 'Tailoring Patterns',
        '3': 'Engineering Schematics',
        '4': 'Blacksmithing Plans',
        '5': 'Cooking Recipes',
        '6': 'Alchemy Recipes',
        '7': 'First Aid Books',
        '8': 'Enchanting Formulae',
        '9': 'Fishing Books',
        '10': 'Jewelcrafting Designs',
        '11': 'Inscription Techniques',
        '12': 'Mining Guides'
    },
    'Gems': {
        '0': 'Red',
        '1': 'Blue',
        '2': 'Yellow',
        '3': 'Purple',
        '4': 'Green',
        '5': 'Orange',
        '6': 'Meta',
        '7': 'Simple',
        '8': 'Prismatic',
        '9': 'Sha-Touched',
        '10': 'Cogwheel',
        '11': 'Other',
        '-8': 'Iron Relics',
        '-9': 'Blood Relics',
        '-10': 'Shadow Relics',
        '-11': 'Fel Relics',
        '-12': 'Arcane Relics',
        '-13': 'Frost Relics',
        '-14': 'Fire Relics',
        '-15': 'Water Relics',
        '-16': 'Life Relics',
        '-17': 'Storm Relics',
        '-18': 'Holy Relics'
    },
    'Miscellaneous': {
        '1': 'Reagents',
        '2': 'Companions',
        '3': 'Holiday',
        '4': 'Other',
        '5': 'Mounts',
        '-2': 'Armor Tokens',
        '11': 'Other'
    }
}

sources = {
    'Vendor': 7,
    # 'Crafted': 3,
    # 'Any': 1
}

source_types = {
    5: 'Vendor',
    2: 'Drop'
}

expansions = {
    'Classic': 1,
    'TBC': 2,
    'WoTLK': 3,
    'Cata': 4,
    'MoP': 5,
    'WoD': 6,
    'Legion': 7,
    'BFA': 8
}

if __name__ == '__main__':
    for source in sources:
        df_main = pandas.DataFrame(
            columns=['classs', 'id', 'name', 'slot', 'source', 'subclass', 'expansion'])
        for cat in item_cats:
            for xpac in expansions:
                for slot in item_slots[cat]:
                    search_url = construct_wowdb_url(item_cats[cat], item_slots[cat][slot], expansions[xpac], source)
                    return_html = read_source_from_url(search_url)
                    df = read_item_table_from_wowdb_url(return_html, expansions[xpac])

                    if not df.empty:
                        # Remove Darkmoon Trinkets, the only items with Source == 'Created'
                        #df = df[2 not in df.source.tolist()]
                        df_main = df_main.append(df)
            outfile = f'{source}_{cat}.dat'
            df_main = df_main.reset_index(drop=True)
            save_df_as_tsm_groups(df_main, outfile, source, cat)
            df_main = df_main.truncate(before=-1,after=-1)