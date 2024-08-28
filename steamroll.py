import argparse

BASE92 = "~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}"
SAFECHARS = ["~", "^", "`", "@", "{", "|", "}", "[", "]", "<", ">", "=", "*", "+", "-", "#", "%", "$", "&", "'", "(", ")", "_", "/", ":", ";", "!", "?", "," , ".", "~~", "~^", "~`", "~@", "~{", "~|", "~}", "~[", "~]", "~<", "~>", "~=", "~*", "~+", "~-", "~#", "~%", "~$", "~&", "~'", "~(", "~)", "~_", "~/", "~:", "~;", "~!", "~?", "~,", "~."]

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

def fread(path):
    data = None
    with open(path, "rb") as file:
        data = file.read()
    data = data.decode("ascii", "ignore").replace("\r\n", "\n")
    return data

def fwrite(data, path):
    with open(path, "w") as file:
        file.write(data)

def getSafeChar(chars):
    keepSearching = False
    searchDoubles = False
    for idCharIndex in range(len(SAFECHARS)):
        keepSearching = False
        for index in range(len(chars)):
            if searchDoubles == False:
                if chars[index] == SAFECHARS[idCharIndex]:
                    keepSearching = True
                    break
            else:
                if index < len(chars) - 1:
                    if f"{chars[index]}{chars[index + 1]}" == SAFECHARS[idCharIndex]:
                        keepSearching = True
                        break
            index += 1

        if idCharIndex >= 29:
            searchDoubles = True

        if keepSearching == False:
            return SAFECHARS[idCharIndex]
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
            # 1 tokenID digit + 3 id characters + initial occurance of token + (ideal tokenmap * (number of occurances - 1))
            compressed = 1 + (idCharacterLength * 3) + len(token[0]) + (3 * (token[1] - 1))
            uncompressed = len(token[0]) * token[1]
            ratio = compressed / uncompressed
            
            result[base92ID] = [token[0], ratio]
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

    keyedRankedTokenmaps = {}
    index = 0
    # give proper base92 ids to each tokenmap
    for tokenmap in rankedTokenmaps:
        if tokenmap[1] < 1.0:
            base92ID = base92(index)
            keyedRankedTokenmaps[base92ID] = tokenmap
            index += 1

    return keyedRankedTokenmaps

def compressToken(chars, tokenID, tokenmap, safechar):
    if tokenmap[1] < 1.0:

        occurances = chars.count(tokenmap[0])
        if occurances > 1:
            fullTokenmap = f"{safechar}{tokenID}{safechar}{tokenmap[0]}{safechar}"
            firstInstance = chars.replace(tokenmap[0], fullTokenmap, 1)
            splitChars = firstInstance.split(fullTokenmap)  
            compressedSplit = splitChars[1].replace(tokenmap[0], f"{safechar}{tokenID}{safechar}")
            combinedCompressedChars = splitChars[0] + fullTokenmap + compressedSplit
            return [combinedCompressedChars, True]
        else:
            return [chars, False]

def steamroll(chars):
    safechar = getSafeChar(chars)

    # examine all relevant token sizes to find compression ratios we can obtain from compressing each
    rankedTokenmaps = []
    searchLength = 4
    continueRanking = True
    while continueRanking == True:
        nextRanking = getTokenFrequency(chars, searchLength, len(safechar))
        if len(nextRanking) > 0:
            rankedTokenmaps.append(nextRanking)
        else:
            continueRanking = False
        searchLength += 1

    # compare compression ratio across all token sizes and return the order we will compress in
    rankedTokenmaps = rankAllTokenmaps(rankedTokenmaps)

    # iteratively compress the char buffer by each token if it is still valid
    tokenCounter = 0
    compressedChars = chars
    for originalTokenID in rankedTokenmaps:
        compressionResult = compressToken(compressedChars, base92(tokenCounter), rankedTokenmaps[originalTokenID], safechar)
        compressedChars = compressionResult[0]
        incrementStatus = compressionResult[1]
        if incrementStatus:
            tokenCounter += 1
    
    compressedChars = f"{safechar}{compressedChars}{safechar}"

    return compressedChars

def findNextTokenmap(chars, safechar, tokenCounter):
    tokenID = base92(tokenCounter)
    split = chars.split(f"{safechar}{tokenID}{safechar}")
    if len(split) > 1:
        originalToken = split[1].split(safechar)
        return [True, [tokenID, originalToken[0]]]
    else:
        return [False]

def uncompressTokenmap(chars, tokenmap, safechar):
    reconstructedTokenmap = f"{safechar}{tokenmap[0]}{safechar}{tokenmap[1]}{safechar}"
    uncompressedChars = chars.replace(reconstructedTokenmap, tokenmap[1])
    return uncompressedChars

def uncompressTokens(chars, tokenmap, safechar):
    tokenID = f"{safechar}{tokenmap[0]}{safechar}"
    uncompressedChars = chars.replace(tokenID, tokenmap[1])
    return uncompressedChars

def unsteamroll(chars):
    safecharGuess = ""
    if chars[:2] == chars[-2:] and chars[:2] in SAFECHARS[30:]:
        safecharGuess = chars[:2]
    elif chars[0] == chars[-1]:
        safecharGuess = chars[0]
    else:
        print("This is not a valid steamrolled file and cannot be uncompressed.")
        return False

    tokenmaps = []
    tokenCounter = 0
    keepSearching = True
    while keepSearching:
        foundNextTokenmap = findNextTokenmap(chars[len(safecharGuess):-len(safecharGuess)], safecharGuess, tokenCounter)
        if foundNextTokenmap[0]:
            tokenmaps.append(foundNextTokenmap[1])
            tokenCounter += 1
        else:
            keepSearching = False

    uncompressedChars = chars

    # first uncompress/fix the initial occurances of the tokenmaps to avoid safechar collisions
    for tokenmap in tokenmaps:
        uncompressedChars = uncompressTokenmap(uncompressedChars, tokenmap, safecharGuess)
    
    # second actually uncompress all the tokenIDs
    for tokenmap in tokenmaps:
        uncompressedChars = uncompressTokens(uncompressedChars, tokenmap, safecharGuess)

    return uncompressedChars[len(safecharGuess):-len(safecharGuess)]

def main(source, isCompress, isUncompress, isClean):
    chars = fread(source)

    if isCompress:
        compressedText = steamroll(chars)
        fwrite(compressedText, r"C:\\Working\\steamroll\\testCompressed.txt")
    
    if isUncompress:
        uncompressedText = unsteamroll(chars)
        if uncompressedText:
            fwrite(uncompressedText, r"C:\\Working\\steamroll\\testUncompressed.txt")
        else:
            print("Failed to write uncompressed file.")

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
