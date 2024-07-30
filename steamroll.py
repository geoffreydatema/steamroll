import argparse

steamrolldata = {}
steamrolltokencounts = {}

BASE92 = "~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&'()*+,-./:<=>?@[]_`{|}"

def base90(decimal):
    base90String = ""
    if decimal >= 0:
        while True:
            base90String = f"{BASE92[decimal % 90]}{base90String}"
            decimal //= 90
            if decimal <= 0:
                break
        return base90String
    else:
        print("cannot convert negative decimal to base92")
        return None

def fread(path):
    data = None
    with open(path, "rb") as file:
        data = file.read()
    data = data.decode("ascii", "ignore").replace("\r\n", "\n")
    return data

def fwrite(data, path):
    with open(path, "w") as file:
        file.write(data)

def steamroll(steamrolldata, steamrolltokencounts, chars):
    tokens = chars.split(" ")
    index = 0
    totalTokens = 0

    for token in tokens:
        if len(token) > 3:
            if token not in steamrolldata.values():
                base92Index = base90(index)
                steamrolldata[base92Index] = token
                steamrolltokencounts[base92Index] = 1
                index += 1
            else:
                for key in steamrolldata.keys():
                    if steamrolldata[key] == token:
                        steamrolltokencounts[key] += 1
        totalTokens += 1

    tokensToRemove = []
    for key in steamrolldata.keys():
        if steamrolltokencounts[key] <= 1:
            tokensToRemove.append(key)
        # else:
        #     print(f"{steamrolldata[key]} : {steamrolltokencounts[key]}")

    for key in tokensToRemove:
        del steamrolldata[key]
        del steamrolltokencounts[key]

    renumberedSteamrollData = {}
    renumberedSteamrollTokenCounts = {}
    
    index = 0
    for key in steamrolldata:
        renumberedSteamrollData[base90(index)] = steamrolldata[key]
        renumberedSteamrollTokenCounts[base90(index)] = steamrolltokencounts[key]
        index += 1

    steamrolldata = renumberedSteamrollData
    steamrolltokencounts = renumberedSteamrollTokenCounts

    tokenQueue = [""]
    for key in steamrolldata.keys():
        tokenQueue[0] += f"^{key}^{steamrolldata[key]}"
    tokenQueue[0] += ";"
    for token in tokens:
        addedToken = False
        for key in steamrolldata.keys():
            if steamrolldata[key] == token:
                tokenQueue.append(f"^{key}^ ")
                addedToken = True
                break
        if addedToken == False:
            tokenQueue.append(f"{token} ")
    # print(steamrolldata)
    # print(steamrolltokencounts)
    # print(index)
    # print(totalTokens)
    # print(tokenQueue)
    tokenQueue[-1] = tokenQueue[-1][:-1]
    return "".join(tokenQueue)

def unsteamroll(steamrolldata, steamrolltokencounts, chars):
    headerSplit = chars.split(";")
    header = headerSplit[0].split("^")[1:]
    data = headerSplit[1]
    while len(header) > 0:
        steamrolldata[header[0]] = header[1]
        header = header[2:]

    uncompressedDataQueue = []
    nextToken = ""
    startMappedToken = False
    for char in data:
        if char == "^":
            if startMappedToken == False:
                startMappedToken = True
                uncompressedDataQueue.append(nextToken)
                nextToken = ""
            elif startMappedToken == True:
                startMappedToken = False
                uncompressedDataQueue.append(steamrolldata[nextToken[1:]])
                nextToken = ""
                continue
        nextToken += char
    if nextToken:
        uncompressedDataQueue.append(nextToken)

    return "".join(uncompressedDataQueue)

def main(source, isCompress, isUncompress, isClean):
    chars = fread(source)

    if isCompress:
        compressedText = steamroll(steamrolldata, steamrolltokencounts, chars)
        fwrite(compressedText, r"C:\\Working\\steamroll\\testCompressed.txt")
    
    if isUncompress:
        uncompressedText = unsteamroll(steamrolldata, steamrolltokencounts, chars)
        fwrite(uncompressedText, r"C:\\Working\\steamroll\\testUncompressed.txt")

    if isClean:
        fwrite(chars, r"C:\\Working\\steamroll\\testCleaned.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", help="Plain text file to operate on.")
    parser.add_argument("-c", "--compress", action="store_true", help="Compress the file.")
    parser.add_argument("-u", "--uncompress", action="store_true", help="Uncompress the file.")
    parser.add_argument("-cl", "--clean", action="store_true", help="Clean the file of non-ascii characters.")
    args = parser.parse_args()
    main(args.source, args.compress, args.uncompress, args.clean)

# !* renumber tokens to optimize how many characters can be represented by the smallest base90 digit
# !* only keep a token map if it results in compression
# !* pull words out of punctuation to compress them