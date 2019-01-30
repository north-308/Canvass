import csv
f = open('locations.txt', 'w')
with open('city_of_hampstead.csv','r') as file:
    reader = csv.reader(file)
    i = 0
    input = ''
    for line in reader:
        if i % 5 is 0:
            input += '[\n\"'+line[2]+','+line[3]+','+line[5]+','+line[7]+','+line[8]+'\",\n{\n\"lat\": '+line[1]+',\n\"lng\":'+line[0]\
            +"\n}\n],"
        if i is 120:
            break
        i += 1
f.write(input)
f.close()




  # [
  #           "203,Wyckoff Ave,Ithaca,NY,14850",
  #           {
  #               "lat": 42.4542022,
  #               "lng": -76.48348709999999
  #           }
  #       ]