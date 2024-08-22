import argparse

# steamrolldata = {}
# steamrolltokencounts = {}

BASE92 = "~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}"
IDCHARS = ["~", "^", "`", "@", "{", "|", "}", "[", "]", "<", ">", "=", "*", "+", "-", "#", "%", "$", "&", "'", "(", ")", "_", "/", ":", ";", "!", "?", "," , ".", "~~", "~^", "~`", "~@", "~{", "~|", "~}", "~[", "~]", "~<", "~>", "~=", "~*", "~+", "~-", "~#", "~%", "~$", "~&", "~'", "~(", "~)", "~_", "~/", "~:", "~;", "~!", "~?", "~,", "~."]

# POWERSOF90 = [90, 8100, 729000, 65610000, 5904900000]

def base92(decimal):
    base92String = ""
    if decimal >= 0:
        while True:
            base92String = f"{BASE92[decimal % 92]}{base92String}"
            decimal //= 92
            if decimal <= 0:
                break
        return base92String
    else:
        print("cannot convert negative decimal to base92")
        return None

# def fromBase90(base90):
#     base90Decimals = {'~': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25, 'Z': 26, 'a': 27, 'b': 28, 'c': 29, 'd': 30, 'e': 31, 'f': 32, 'g': 33, 'h': 34, 'i': 35, 'j': 36, 'k': 37, 'l': 38, 'm': 39, 'n': 40, 'o': 41, 'p': 42, 'q': 43, 'r': 44, 's': 45, 't': 46, 'u': 47, 'v': 48, 'w': 49, 'x': 50, 'y': 51, 'z': 52, '0': 53, '1': 54, '2': 55, '3': 56, '4': 57, '5': 58, '6': 59, '7': 60, '8': 61, '9': 62, '!': 63, '#': 64, '$': 65, '%': 66, '&': 67, "'": 68, '(': 69, ')': 70, '*': 71, '+': 72, ',': 73, '-': 74, '.': 75, '/': 76, ':': 77, '<': 78, '=': 79, '>': 80, '?': 81, '@': 82, '[': 83, ']': 84, '_': 85, '': 86, '{': 87, '|': 88, '}': 89}
#     decimal = 0
#     power = 0
#     for char in reversed(base90):
#         decimal += base90Decimals[char] * (90 ** power)
#         power += 1
#     return decimal

def fread(path):
    data = None
    with open(path, "rb") as file:
        data = file.read()
    data = data.decode("ascii", "ignore").replace("\r\n", "\n")
    return data

def fwrite(data, path):
    with open(path, "w") as file:
        file.write(data)

def steamrollold(steamrolldata, steamrolltokencounts, chars):
    tokens = chars.split(" ")
    index = 0
    totalTokens = 0

    # map all words to a base90 id
    for token in tokens:
        if len(token) > 4:
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

    # flag all tokens that map to a word that isn't repeated, so that we can remove them
    tokensToRemove = []
    for key in steamrolldata.keys():
        numberOfBytesOriginal = len(steamrolldata[key]) * steamrolltokencounts[key]
        numberOfBytesCompressed = (len(steamrolldata[key]) + len(key) + 1) + ((len(key) + 1) * steamrolltokencounts[key])
        ratio = numberOfBytesCompressed / numberOfBytesOriginal
        
        if ratio >= 1:
            tokensToRemove.append(key)

    # remove mapped tokens that won't result in net compression
    for key in tokensToRemove:
        del steamrolldata[key]
        del steamrolltokencounts[key]

    # renumber all mapped tokens starting from 0 so that we use as few base90 digits to map to them
    renumberedSteamrollData = {}
    renumberedSteamrollTokenCounts = {}
    
    index = 0
    for key in steamrolldata:
        renumberedSteamrollData[base90(index)] = steamrolldata[key]
        renumberedSteamrollTokenCounts[base90(index)] = steamrolltokencounts[key]
        index += 1

    steamrolldata = renumberedSteamrollData
    steamrolltokencounts = renumberedSteamrollTokenCounts

    # write the token map to the start of the file
    tokenQueue = [""]
    for key in steamrolldata.keys():
        tokenQueue[0] += f"^{key}{steamrolldata[key]}"
    tokenQueue[0] += ";"

    # create a queue of tokens, subbing in the mapped id for compressed tokens
    for token in tokens:
        addedToken = False
        for key in steamrolldata.keys():
            if steamrolldata[key] == token:
                tokenQueue.append(f"^{key} ")
                addedToken = True
                break
        if addedToken == False:
            tokenQueue.append(f"{token} ")
    tokenQueue[-1] = tokenQueue[-1][:-1]

    return "".join(tokenQueue)

def getSafeChar(chars):
    keepSearching = False
    searchDoubles = False
    for idCharIndex in range(len(IDCHARS)):
        keepSearching = False
        for index in range(len(chars)):
            if searchDoubles == False:
                if chars[index] == IDCHARS[idCharIndex]:
                    keepSearching = True
                    break
            else:
                if index < len(chars) - 1:
                    if f"{chars[index]}{chars[index + 1]}" == IDCHARS[idCharIndex]:
                        keepSearching = True
                        break
            index += 1

        if idCharIndex >= 29:
            searchDoubles = True

        if keepSearching == False:
            return IDCHARS[idCharIndex]
    print("Could not find a safe character for mapping tokens. Unfortunatly this file cannot be compressed.")
    return None

def sortByFrequency(dictionary):
    return dict(sorted(dictionary.items(), key=lambda item: item[1][1], reverse=True))

def getCompressionRatios(tokenmap, idCharacterLength):
    result = {}
    index = 0
    for tokenID in tokenmap.keys():
        if tokenmap[tokenID][1] > 1:
            base92ID = base92(index)
            token = tokenmap[tokenID]
            # calculate the compressed token size using the best case scenario which would be
            # using a single digit to represent the token (in reality, it may end up being larger)
            # 1 tokenmap digit + 3 id characters + initial occurance of token + (ideal tokenmap * (number of occurances - 1))
            compressed = 1 + (idCharacterLength * 3) + len(token[0]) + (3 * (token[1] - 1))
            uncompressed = len(token[0]) * token[1]
            result[base92ID] = [token[0], compressed / uncompressed]
            print(f"{base92ID} {token} {compressed} {uncompressed} {result[base92ID]}")
            index += 1

    return result

def getTokenFrequency(chars, tokenLength, idCharacterLength):
    offset = 0
    uniqueTokens = {}
    tokenList = {}
    for index in range(len(chars)):
        if index < len(chars) - tokenLength:
            token = ""
            for i in range(tokenLength):
                token += chars[index + i + offset]
            if token not in uniqueTokens.values():
                uniqueTokens[base92(index)] = token
            tokenList[base92(index)] = token

    tokenmap = {}
    for i in uniqueTokens.keys():
        tokenmap[i] = [uniqueTokens[i], 0]
        for j in tokenList.keys():
            if uniqueTokens[i] == tokenList[j]:
                tokenmap[i][1] += 1

    sortedTokenmap = sortByFrequency(tokenmap)
    tokenmapRatios = getCompressionRatios(sortedTokenmap, idCharacterLength)
    return tokenmapRatios

def rankAllTokenmaps(allTokenmaps):

    rankedTokenmaps = []

    # flatten dictionaries to a single list
    for tokenmap in allTokenmaps:
        for key in tokenmap.keys():
            rankedTokenmaps.append(tokenmap[key])

    # sort tokenmaps by compression ratio
    rankedTokenmaps.sort(key=lambda x: x[1])

    return rankedTokenmaps

def steamroll(chars):
    idChar = getSafeChar(chars)

    # examine all relevant token sizes to find compression ratios we can obtain from compressing each
    rankedTokenmaps = []
    searchLength = 3
    continueRanking = True
    while continueRanking == True:
        nextRanking = getTokenFrequency(chars, searchLength, len(idChar))
        if len(nextRanking) > 0:
            rankedTokenmaps.append(nextRanking)
        else:
            continueRanking = False
        searchLength += 1

    # compare compression ratio across all token sizes and return the order we will compress in
    rankedTokenmaps = rankAllTokenmaps(rankedTokenmaps)
    
    # print(rankedTokenmaps)

    # DONE find compression ratios for token size of three, four, fives etc, until the size of token gives zero net compression
    # DONE rank all the tokenmaps by most bytes compressed by the fewest id digits
    # !* compress by each tokenmap in order, if it's still valid (because a previous compression may have invalidated it)
    # !* maybe at the end reevaluate the new ranking of best mappings and continue the process until no more compression is obtained

def unsteamrollold(steamrolldata, chars):
    # split header from data
    headerSplit = chars.split(";")
    
    # read in tokenmap
    header = headerSplit[0].split("^")[1:]
    data = headerSplit[1]
    mappedTokenCounter = 0
    while len(header) > 0:
        if mappedTokenCounter < POWERSOF90[0]:
            digitCount = 1
        elif mappedTokenCounter < POWERSOF90[1]:
            digitCount = 2
        elif mappedTokenCounter < POWERSOF90[2]:
            digitCount = 3
        elif mappedTokenCounter < POWERSOF90[3]:
            digitCount = 4
        elif mappedTokenCounter < POWERSOF90[4]:
            digitCount = 5
        else:
            print("cannot handle over 5904900000 mapped tokens")
        
        base90Index = header[0][:digitCount]
        steamrolldata[base90Index] = header[0][digitCount:]
        header = header[1:]
        mappedTokenCounter += 1

    # read in mixed tokens, uncompressing mapped tokens using the tokenmap
    data = data.split(" ")
    uncompressedDataQueue = []

    for token in data:
        if token[0] == "^":
            uncompressedDataQueue.append(f"{steamrolldata[token[1:]]} ")
        else:
            uncompressedDataQueue.append(f"{token} ")
    uncompressedDataQueue[-1] = uncompressedDataQueue[-1][:-1]

    return "".join(uncompressedDataQueue)

def main(source, isCompress, isUncompress, isClean):
    chars = fread(source)

    if isCompress:
        compressedText = steamroll(chars)
        # fwrite(compressedText, r"C:\\Working\\steamroll\\testCompressed.txt")
    
    if isUncompress:
        pass
        # uncompressedText = unsteamroll(steamrolldata, chars)
        # fwrite(uncompressedText, r"C:\\Working\\steamroll\\testUncompressed.txt")

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

# !* sort mapped tokens to optimize storing the most repetitions with the smallest ids
# !* pull words out of punctuation to compress them?
# !* handle ; in mapped tokens