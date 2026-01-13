import json
import os
import shutil
import requests
from time import sleep
import numpy as np

#
# PARAMETERS
#

# How many times an emoji had to be used to get downloaded
minimum_usages = 7
# How long to wait (in seconds) between downloads
time_between_emoji_downloads = 0.025
# How to split emojis based on usage, eg. 0.80 creates one group for emoji that were used in the top 20% of all emoji
splits = [0.80, 0.60, 0.40]

#
# CODE
#
names = [x[0] for x in os.walk("Messages")][1::]
seen_emoji = {}
emoji_names = {}
message_count = 0

def handle(message_content):
    """
    :type message_content: str
    """
    global message_count
    message_count = message_count + 1
    start = 0
    while True:
        i = message_content.find("<:", start)
        if i == -1:
            break

        start_id = message_content.index(":", i + 2)
        end_id = message_content.index(">", i + 2)
        
        if start_id == -1 or end_id == -1:
            start = start + 2
            break

        start = end_id
        id = message_content[start_id+1:end_id]
        name = message_content[i+2:start_id]

        if id not in seen_emoji:
            seen_emoji[id] = 1
        else:
            seen_emoji[id] = seen_emoji[id] + 1
        emoji_names[id] = name
    print(f"\rParsed {message_count} messages with {len(seen_emoji)} emojis used a total of {sum(seen_emoji.values())} times", end="")

for dir in names:
    with open(f"{dir}/messages.json", "r", encoding='utf-8') as m_list:
        for m in json.load(m_list):
            handle(m["Contents"])

print("\nDone reading messages")
old_count = len(seen_emoji)
seen_emoji = dict([item for item in seen_emoji.items() if item[1] >= minimum_usages])
new_count = len(seen_emoji)
print(f"Removed {old_count - new_count} emoji that did not meet minimum usages count, {new_count} emojis to download with total usages of {sum(seen_emoji.values())}")

thresholds = np.quantile(list(seen_emoji.values()), splits)

root = "Emoji_Dump"
if os.path.isdir(root):
    shutil.rmtree(root)
for x in range(len(thresholds)+1):
    os.makedirs(f"{root}")
    

for emoji_id in seen_emoji:
    count = seen_emoji[emoji_id]
    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.webp"

    q = len(thresholds) + 1
    for i in range(len(thresholds)):
        t = thresholds[i]
        if count >= t:
            q = i + 1
            break

    print(f"\rDownloading emoji from split {q}: {emoji_id.ljust(19)}", end="")

    result = requests.get(url)
    result.raise_for_status()
    with open(f"{root}/split_{q}/{emoji_names[emoji_id]}.webp", "wb") as f:
        f.write(result.content)

    sleep(time_between_emoji_downloads)

print("\nDone!")
