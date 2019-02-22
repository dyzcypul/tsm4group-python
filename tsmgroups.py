import json
import time
import urllib.request

import pandas
from bs4 import BeautifulSoup

debug = True

expansions = {
    '1': 'Classic',
    '2': 'TBC',
    '3': 'WoTLK',
    '4': 'Cata',
    '5': 'MoP',
    '6': 'WoD',
    '7': 'Legion',
    '8': 'BFA'
}

item_cats = {
    'Weapons': 'weapons',
    'Armor': 'armor',
    # 'Containers': 'containers',
    # 'Consumables': 'consumable-items',
    # 'Trade Goods': 'trade-goods',
    # 'Recipes': 'recipe-items',
    # 'Gems': 'gems',
    # 'Miscellaneous': 'miscellaneous-items'
}

item_slots = {
    'Weapons': {
        '21': 'Main Hand',
        '22': 'Off Hand',
        '13': 'One-Hand',
        '15': 'Ranged',
        '25': 'Thrown',
        '17': 'Two-Hand'
    },
    'Armor': {
        '16': 'Back',
        '5': 'Chest',
        '8': 'Feet',
        '11': 'Finger',
        '10': 'Hands',
        '1': 'Head',
        '23': 'Off-hand',
        '7': 'Legs',
        '2': 'Neck',
        '14': 'Shield',
        '4': 'Shirt',
        '3': 'Shoulder',
        '19': 'Tabard',
        '12': 'Trinket',
        '6': 'Waist',
        '9': 'Wrist'
    },
    'Containers': {
        '18': 'Bag'
    },
    'Consumables': {
        '0': 'Consumable'
    },
    'Trade Goods': {
        '0': 'Trade Goods'
    },
    'Recipes': {
        '0': 'Recipe'
    },
    'Gems': {
        '0': 'Gem'
    },
    'Miscellaneous': {
        '0': 'Miscellaneous'
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

item_source_lookup = {
    '2': 'Drop'
}

item_sources = {
    'Drop': 4
}

def construct_wowdb_url(itype, slot, expansion, source):
    """ Construct wowdb-url for given filter settings. """
    #url = f"https://www.wowdb.com/items/{itype}?filter-bind={bind}&filter-expansion={xpac_filt}&filter-slot={slot_filt}&filter-source={sour_filt}"
    url = f'https://www.wowhead.com/{itype}'
    if itype == "armor" or itype == "weapons":
        url += f'/slot:{slot}'
    if source == 4:
        url += f'/live-only:on?filter=166:3:161:162:128;{expansion}:1:1:2:{source};0:0:0:0:0'
    else:
        url = ""

    if debug:
        print(url)
    return url

def read_source_from_url(url):
    """ Read URL and return source_code as decoded str. """
    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, 'html.parser')
    
    parsed_table = soup.find_all('script', type="text/javascript")
    
    output = str(parsed_table).partition('var listviewitems = [{')[2].rpartition('}];')[0]
    output = output.replace("firstseenpatch", "\"firstseenpatch\"")
    output = output.replace("cost", "\"cost\"")
    if debug:
        print(output)
    if output:
        return json.loads('[{%s}]' % (output))
    else:
        return ""

def read_item_table(data):
    if data:
        if debug:
            print("Full DataFrane")
        df = pandas.DataFrame(data, 
            columns=['id', 'subclass'])
    else:
        if debug:
            print("Empty DataFrame")
        return pandas.DataFrame(
            columns=['id', 'subclass'])

    if debug:
        print(df)

    return df

def save_df_as_tsm_groups(df_main, outfile, cat, xpac, slot, source):
    out_str = ""

    df_main = df_main.astype({"subclass": str})
    df_main = df_main.astype({"id": int})

    slot_types_as_subgroups = ['Finger', 'Trinket', 'Back', 'Cloaks', 
                               'Neck', 'Shirt', 'Tabard', 'Off-hand', 'Shield', 'One-Hand']

    subclass = df_main['subclass'].unique()
    for sub in subclass:
        df = df_main.loc[
            (df_main['subclass'] == sub)
        ]

        if debug:
            print(df)

        if slot not in slot_types_as_subgroups:
            out_str += f'group:{xpac}`{cat}`{slot}`{item_types[cat][sub]}`{source},'
        else:
            out_str += f'group:{xpac}`{cat}`{item_types[cat][sub]}`{source},'

        item_ids = df['id'].values
        for item_id in item_ids:
            out_str += f'i:{item_id},'

        if debug:
            print(out_str)

    if not out_str == "":
        with open(outfile, 'w') as f:
            f.writelines(out_str)

if __name__ == '__main__':
    for xpac in expansions:
        for cat in item_cats:
            outfile = ""
            df_main = pandas.DataFrame(
                columns=['id', 'subclass'])
            for slot in item_slots[cat]:
                for source in item_sources:
                    search_url = construct_wowdb_url(item_cats[cat], slot, xpac, item_sources[source])
                    if search_url:
                        df = read_item_table(read_source_from_url(search_url))
                        if not df.empty:
                            df_main = df_main.append(df)
                        outfile = f'{expansions[xpac]}_{cat}_{source}.dat'
            df_main = df_main.reset_index(drop=True)
            save_df_as_tsm_groups(df_main, outfile, cat, expansions[xpac], item_slots[cat][slot], source)
            df_main = df_main.truncate(before=-1,after=-1)

