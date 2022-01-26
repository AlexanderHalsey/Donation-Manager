# Code to generate contacts and donations, file added to demonstrate working through

import requests
import bs4
import re
import random
import json
import datetime

first_names = []
last_names = []

res_fn = requests.get("https://www.chroniclelive.co.uk/news/uk-news/top-100-most-popular-baby-20811799")
res_ln = requests.get("https://www.thoughtco.com/common-us-surnames-and-their-meanings-1422658")
soup_fn = bs4.BeautifulSoup(res_fn.text,"lxml")
soup_ln = bs4.BeautifulSoup(res_ln.text,"lxml")

for name in soup_fn.select("ol li")[5:]:
    n = re.search(r"\w*",name.text)
    first_names.append(n.group())

for last_name in soup_ln.select(".mntl-sc-list-item-title"):
    n = re.search(r"\S+", last_name.text)
    last_names.append(n.group().lower().capitalize())
    
random.shuffle(first_names)
random.shuffle(last_names)

names = [f+" "+l for f,l in list(zip(first_names, last_names))]

with open("dataset/100_phone_numbers.txt", "r") as f:   
    f.seek(0) 
    phones = eval(f.read())
with open("dataset/100_addresses.txt", "r") as f:
    f.seek(0)
    addresses = eval(f.read())

#names = names[:10]
#addresses = addresses[:10]
#phones = phones[:10]

# random email function for each contact
def email(data):
    full_name = data.lower().split(" ")
    initials = [list(filter(lambda x: x.isupper(), [char for char in data]))[0].lower() for data in data.split(" ")]
    
    first_name = ["", full_name[0], initials[0]]
    last_name = ["", full_name[1], initials[1]]
    separator = ["",".","_"]
    random_number = ["",str(random.randint(1,999))]
    domain = ["@domain"+str(random.randint(1,9))+".com"]
    
    pending = True
    while pending:
        email = ""
        for content in [first_name, separator, last_name, separator, random_number, domain]:
            email += random.choice(content)
        if email[0] in [".","_"] or email.split("@")[0].endswith("_") or email.split("@")[0].endswith(".") or len(email.split("@")[0]) < 4:
            continue
        elif (first_name,last_name) == ("","") or (first_name,random_number) == ("","") or (last_name,random_number) == ("",""):
            continue
        elif "._" in email or "_." in email:
            continue
        else:
            pending = False
    
    return email

# contact details field
details = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nisi quis eleifend quam adipiscing. Elit ut aliquam purus sit amet luctus venenatis. Odio facilisis mauris sit amet massa vitae. Sem integer vitae justo eget magna fermentum iaculis. Nunc aliquet bibendum enim facilisis gravida neque convallis a. Orci nulla pellentesque dignissim enim. Sed vulputate odio ut enim blandit volutpat. Duis at tellus at urna condimentum mattis. Amet commodo nulla facilisi nullam vehicula ipsum a arcu. Pellentesque sit amet porttitor eget dolor. Nisl vel pretium lectus quam id leo in vitae turpis. Nisl condimentum id venenatis a. Amet facilisis magna etiam tempor orci eu lobortis. Ornare massa eget egestas purus viverra accumsan. Arcu bibendum at varius vel pharetra vel turpis. Turpis in eu mi bibendum neque. Enim eu turpis egestas pretium aenean pharetra magna. Egestas maecenas pharetra convallis posuere. Volutpat lacus laoreet non curabitur. Mattis vulputate enim nulla aliquet porttitor lacus. Mauris pellentesque pulvinar pellentesque habitant morbi. Nisl tincidunt eget nullam non nisi est. Nec feugiat in fermentum posuere urna nec tincidunt praesent. Nibh nisl condimentum id venenatis a condimentum vitae sapien pellentesque. Quis eleifend quam adipiscing vitae proin sagittis nisl. Eget nulla facilisi etiam dignissim diam quis enim. Nulla porttitor massa id neque aliquam vestibulum morbi blandit cursus. Nunc faucibus a pellentesque sit amet. Pellentesque eu tincidunt tortor aliquam nulla facilisi. Suspendisse interdum consectetur libero id faucibus. Diam quam nulla porttitor massa id neque aliquam vestibulum morbi. Ante metus dictum at tempor commodo ullamcorper a lacus vestibulum. Ultrices sagittis orci a scelerisque. Non enim praesent elementum facilisis leo vel. Scelerisque eleifend donec pretium vulputate sapien nec sagittis. Vitae elementum curabitur vitae nunc sed velit. Volutpat blandit aliquam etiam erat. Molestie a iaculis at erat pellentesque adipiscing commodo elit. Quisque id diam vel quam elementum pulvinar etiam. Pharetra diam sit amet nisl suscipit adipiscing. Proin libero nunc consequat interdum varius sit amet mattis. Enim ut tellus elementum sagittis vitae et leo duis ut. Magna eget est lorem ipsum dolor sit. At in tellus integer feugiat scelerisque varius morbi enim. Malesuada nunc vel risus commodo viverra maecenas accumsan lacus. Pellentesque nec nam aliquam sem et tortor consequat. Duis at tellus at urna condimentum. Egestas diam in arcu cursus euismod. In iaculis nunc sed augue. Et netus et malesuada fames ac turpis egestas integer eget. Massa vitae tortor condimentum lacinia. Ultrices vitae auctor eu augue. Elit scelerisque mauris pellentesque pulvinar. Sed arcu non odio euismod lacinia at quis risus. Ornare suspendisse sed nisi lacus. In nisl nisi scelerisque eu ultrices. Pharetra magna ac placerat vestibulum lectus. Pretium nibh ipsum consequat nisl. Duis ultricies lacus sed turpis tincidunt id. Eget magna fermentum iaculis eu non diam phasellus vestibulum lorem. Enim facilisis gravida neque convallis a cras. Sit amet tellus cras adipiscing enim. Adipiscing elit pellentesque habitant morbi tristique senectus et. Nisl nisi scelerisque eu ultrices vitae auctor eu augue. Tellus mauris a diam maecenas sed. Lacus laoreet non curabitur gravida arcu. Tincidunt nunc pulvinar sapien et ligula ullamcorper malesuada proin libero. Suscipit tellus mauris a diam maecenas sed enim. Convallis convallis tellus id interdum velit. Accumsan in nisl nisi scelerisque eu. Placerat vestibulum lectus mauris ultrices. Velit sed ullamcorper morbi tincidunt ornare massa eget egestas purus. Risus viverra adipiscing at in tellus integer. Nulla aliquet porttitor lacus luctus accumsan tortor posuere. Enim diam vulputate ut pharetra sit amet aliquam id. Etiam erat velit scelerisque in dictum non. In vitae turpis massa sed elementum tempus egestas sed sed. Velit ut tortor pretium viverra suspendisse potenti nullam ac. Praesent tristique magna sit amet purus gravida. Leo in vitae turpis massa sed elementum tempus egestas sed. Egestas dui id ornare arcu odio ut sem nulla pharetra. Suspendisse sed nisi lacus sed viverra tellus in hac habitasse. Elementum sagittis vitae et leo duis. Et malesuada fames ac turpis egestas. Ipsum faucibus vitae aliquet nec ullamcorper sit amet risus nullam. Urna neque viverra justo nec ultrices dui. Sociis natoque penatibus et magnis dis parturient montes nascetur. Quis varius quam quisque id diam vel. Id aliquet risus feugiat in. Pretium aenean pharetra magna ac placerat vestibulum lectus. Enim nulla aliquet porttitor lacus. Lorem mollis aliquam ut porttitor leo a diam sollicitudin. Nam at lectus urna duis convallis. Commodo nulla facilisi nullam vehicula ipsum a arcu. Dignissim sodales ut eu sem integer vitae. Commodo nulla facilisi nullam vehicula ipsum a arcu. Congue eu consequat ac felis donec et. Orci a scelerisque purus semper. Ultricies mi quis hendrerit dolor magna eget est."
details = details.split(".")
details = [detail+"." for detail in details][:-1]

# random amount for each donation
def amount(index):
    number = 0
    if (index+1) % 10 == 0:
        if (index+1) % 100 == 0:
            if (index+1) % 1000 == 0:
                size = 5
                precision = random.randint(1,4)
            else:
                size = 4
                precision = random.randint(1,3) 
        else:
            size = 3
            precision = random.randint(1,2)
    else:
        size = random.randint(1,2)
        precision = random.randint(1,size+1)
        
    for x in range(max(size,precision)):
        number *= 10
        if x+1 <= precision:
            number += random.randint(1,9)
            
    while len(str(number).split(".")[0]) > size:
        number /= 10
    number = 5*round(number/5,1)
        
    return format(number, ".2f")

# Contact, DonationType, PaymentMode, Organisation Models
profiles = []
contacts = []
payment_modes = []
organisations = []
donation_types = []
forme_du_dons = []
nature_du_dons = []

for index, contact in enumerate(names):
    profiles.append({
        "model": "dm_page.profile",
        "pk": index+1,
        "fields": {
            "seminar_desk_id": random.randint(503245, 48876360),
            "object_type": "PERSON",
            "name": contact,
            "email": email(contact),
            "primary_address": addresses[index],
            "information": details[index],
            "disabled": False,
        }
    })
    contacts.append({
        "model": "dm_page.contact",
        "pk": index+1,
        "fields": {
            "profile": index+1,
            "first_name": contact.split(" ")[0],
            "last_name": contact.split(" ")[1],
            "work_phone_number": phones[index],
        }
    })
don_type_matrix = [(1, "Donation Type 1"), (1, "Donation Type 2"), (1, "Donation Type 3"), (1, "Donation Type 4"), (1, "Donation Type 5"), (2, "Donation Type 6"), (2, "Donation Type 7")]
payment_mode_matrix = ["Payment Mode 1", "Payment Mode 2", "Payment Mode 3", "Payment Mode 4", "Payment Mode 5", "Payment Mode 6"]
forme_des_dons_matrix = [("Form of Donation 1", True), ("Form of Donation 2", False), ("Form of Donation 3", False), ("Form of Donation 4", False)]
nature_des_dons_matrix = [("Nature of Donation 1", True), ("Nature of Donation 2", False), ("Nature of Donation 3", False)]
for i in range(7):
    don_type = {
            "model": "dm_page.donationtype",
            "pk": i + 1,
            "fields": {
                "organisation": "", 
                "name": "",
            }
        }
    mode = {
        "model": "dm_page.paymentmode",
        "pk": i + 1,
        "fields": {
            "payment_mode": "",
        }
    }
    forme = {
        "model": "dm_page.formedudon",
        "pk": i + 1,
        "fields": {
            "name": "",
            "default_value": "",
        }
    }
    nature = {
        "model": "dm_page.naturedudon",
        "pk": i + 1,
        "fields": {
            "name": "",
            "default_value": "",
        }
    }
    if i == 0:
        organisations.append({
            "model": "dm_page.organisation",
            "pk": i + 1,
            "fields": {
                "name": "Org 1",
                "institut_title": "Org Title",
                "institut_street_name": "Org Street Name",
                "institut_town": "Org Town",
                "institut_post_code": "Org Post Code",
                "object_title": "Objectif",
                "object_description": "Objectif Description - Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nisi quis eleifend quam adipiscing. Elit ut aliquam purus sit amet luctus venenatis.",
                "president": "President of Organisation",
                "president_position": "President Position",
            }
        })
    if i == 1:
        organisations.append({
            "model": "dm_page.organisation",
            "pk": i + 1,
            "fields": {
                "name": "Org 2",
            }
        })
    don_type["fields"]["organisation"] = don_type_matrix[i][0]
    don_type["fields"]["name"] = don_type_matrix[i][1]
    donation_types.append(don_type)
    if i == 6:
        continue
    mode["fields"]["payment_mode"] = payment_mode_matrix[i]
    payment_modes.append(mode)
    if i >= 4:
        continue
    forme["fields"]["name"] = forme_des_dons_matrix[i][0]
    forme["fields"]["default_value"] = forme_des_dons_matrix[i][1]
    forme_du_dons.append(forme)
    if i >= 3:
        continue
    nature["fields"]["name"] = nature_des_dons_matrix[i][0]
    nature["fields"]["default_value"] = nature_des_dons_matrix[i][1]  
    nature_du_dons.append(nature)

# Settings and Eligibility Model
settings = []
eligibilities = []
for i in range(1,4):
    setting = {
        "model": "dm_page.paramètre",
        "pk": i,
        "fields": {}
    }
    eligibility = {
        "model": "dm_page.ligibility",
        "pk": i,
        "fields": {}
    }
    if i == 1:
        setting["fields"] = {
            "date_range_start": str(datetime.date(2021, 6, 1)),
            "date_range_end": str(datetime.date(2022, 12, 31)),
        }
        eligibility["fields"] = {
            "organisation": 1,
            "donation_type": 3
        }
    if i == 2:
        setting["fields"] = {
            "release_date": str(datetime.date(2021, 10, 8)),
        } 
        eligibility["fields"] = {
            "organisation": 1,
            "donation_type": 4
        }   
    if i == 3:
        setting["fields"] = {
            "organisation_1": 1,
            "donation_type_1": 3,
            "organisation_2": 1,
            "donation_type_2": 4,
            "organisation_3": 1,
            "donation_type_3": 5,
        }
        eligibility["fields"] = {
            "organisation": 1,
            "donation_type": 5
        }
    settings.append(setting)
    eligibilities.append(eligibility)

# Donation Model
donations = []
for index in range(2319): # variable
    c = random.randint(1, 100)
    o = random.randint(1,2)
    p = random.randint(1,6)
    d = o + random.randint(0,4) if o == 1 else o + random.randint(4,5)
    f = 1
    n = 1

    donations.append({
        "model": "dm_page.donation",
        "pk": index+1,
        "fields": {
            "contact": c,
            "contact_name": names[c-1],
            "date_donated": str(datetime.date.fromordinal(random.randint(737959, 738689))), # variable
            "amount": amount(index),
            "organisation": o,
            "organisation_name": "Org 1" if o==1 else "Org 2",
            "payment_mode": p,
            "payment_mode_name": payment_mode_matrix[p-1],
            "donation_type": d,
            "donation_type_name": don_type_matrix[d-1][1],
            "forme_du_don": f,
            "forme_du_don_name": forme_des_dons_matrix[f-1][0],
            "nature_du_don": n,
            "nature_du_don_name": nature_des_dons_matrix[n-1][0],
            "eligible": (o==1 and d in [3,4,5])
        }
    })


# Serialising data into JSON format for fixture 
with open("dataset/fixtures/Profile.json", "w") as file:
    json.dump(profiles, file)
with open("dataset/fixtures/Contact.json", "w") as file:
    json.dump(contacts, file)
with open("dataset/fixtures/PaymentMode.json", "w") as file:
    json.dump(payment_modes, file)
with open("dataset/fixtures/DonationType.json", "w") as file:
    json.dump(donation_types, file)
with open("dataset/fixtures/Organisation.json", "w") as file:
    json.dump(organisations, file)
with open("dataset/fixtures/NatureDuDon.json", "w") as file:
    json.dump(nature_du_dons, file)
with open("dataset/fixtures/FormeDuDon.json", "w") as file:
    json.dump(forme_du_dons, file)
with open("dataset/fixtures/Paramètre.json", "w") as file:
    json.dump(settings, file)
with open("dataset/fixtures/Eligibility.json", "w") as file:
    json.dump(eligibilities, file)   
with open("dataset/fixtures/Donation.json", "w") as file:
    json.dump(donations, file)