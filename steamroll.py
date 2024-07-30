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

def fromBase92(base92):
    base92Decimals = {'~': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25, 'Z': 26, 'a': 27, 'b': 28, 'c': 29, 'd': 30, 'e': 31, 'f': 32, 'g': 33, 'h': 34, 'i': 35, 'j': 36, 'k': 37, 'l': 38, 'm': 39, 'n': 40, 'o': 41, 'p': 42, 'q': 43, 'r': 44, 's': 45, 't': 46, 'u': 47, 'v': 48, 'w': 49, 'x': 50, 'y': 51, 'z': 52, '0': 53, '1': 54, '2': 55, '3': 56, '4': 57, '5': 58, '6': 59, '7': 60, '8': 61, '9': 62, '!': 63, '#': 64, '$': 65, '%': 66, '&': 67, "'": 68, '(': 69, ')': 70, '*': 71, '+': 72, ',': 73, '-': 74, '.': 75, '/': 76, ':': 77, ';': 78, '<': 79, '=': 80, '>': 81, '?': 82, '@': 83, '[': 84, ']': 85, '^': 86, '_': 87, '`': 88, '{': 89, '|': 90, '}': 91}
    decimal = 0
    power = 0
    for char in reversed(base92):
        decimal += base92Decimals[char] * (92 ** power)
        power += 1
    return decimal

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
            # elif token in steamrolldata.values(): #this can probably just be else for efficiency
            else:
                for key in steamrolldata.keys():
                    if steamrolldata[key] == token:
                        steamrolltokencounts[key] += 1
        totalTokens += 1

    tokensToRemove = []
    for key in steamrolldata.keys():
        if steamrolltokencounts[key] <= 1:
            tokensToRemove.append(key)

    for key in tokensToRemove:
        del steamrolldata[key]
        del steamrolltokencounts[key]

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
