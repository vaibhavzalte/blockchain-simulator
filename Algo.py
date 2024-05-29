import timeit
import struct
# import Message6
# import Message2
# import Message3
# import Message5

from sys import getsizeof
# Initialization Vector IV
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x9b05688c, 0x510e527f, 0x1f83d9ab, 0x5be0cd19]

# H - internal state of hash
H=[]
for i in range (0, len(IV)):
    H.append(IV[i])

cnt=0
total=0
WORDBITS = 32 # bits in a word
WORDBYTES = 4
MASK32BITS = 0Xffffffff
WORDFMT = 'L'
ROUNDS = 10  # Rounds in compression
BLOCKBYTES = 64  # block size 64 bytes

#Rotation Constants
ROT1 =13
ROT2 =17
ROT3 =8
ROT4 =7

WB_ROT1 = WORDBITS - ROT1
WB_ROT2 = WORDBITS - ROT2
WB_ROT3 = WORDBITS - ROT3
WB_ROT4 = WORDBITS - ROT4

# Message word schedule permutations for each round
sigma = [[  0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15 ],
        [ 14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3 ],
        [ 11, 8,12, 0, 5, 2,15,13,10,14, 3, 6, 7, 1, 9, 4 ],
        [  7, 9, 3, 1,13,12,11,14, 2, 6, 5,10, 4, 0,15, 8 ],
        [  9, 0, 5, 7, 2, 4,10,15,14, 1,11,12, 6, 8, 3,13 ],
        [  2,12, 6,10, 0,11, 8, 3, 4,13, 7, 5,15,14, 1, 9 ],
        [ 12, 5, 1,15,14,13, 4,10, 0, 7, 6, 3, 9, 2, 8,11 ],
        [ 13,11, 7,14,12, 1, 3, 9, 5, 0,15, 4, 8, 6, 2,10 ],
        [  6,15,14, 9,11, 3, 0, 8,12, 2,13, 7, 1, 4,10, 5 ],
        [ 10, 2, 8, 4, 7, 6, 1, 5,15,11, 9,14, 3,12,13 ,0 ]]

def Algo(string: bytearray) -> bytearray:
    if isinstance(string, str):
        string = bytearray(string, 'ascii')
    elif isinstance(string, bytes):
        string = bytearray(string)
    elif not isinstance(string, bytearray):
        print("ERROR UNKNOWN STRING FORMAT\n")

    pad = len(string) * 8
    string.append(0x80)
    while (len(string) * 8 + 64) % 512 != 0:
        string.append(0x00)
    
    string += pad.to_bytes(8, 'big')
    assert (len(string) * 8) % 512 == 0, "INCOMPLETE PADDING!"

    blocks = []
    for i in range(0, len(string), 64):
        blocks.append(string[i:i+64])
        
    
    for i in range (0, int(len(blocks)/2)) :
        compress(blocks[i])
        
    
    return (H[0].to_bytes(4,'big')+H[1].to_bytes(4,'big')+H[2].to_bytes(4,'big')+H[3].to_bytes(4,'big')+H[4].to_bytes(4,'big')+H[5].to_bytes(4,'big')+H[6].to_bytes(4,'big')+H[7].to_bytes(4,'big'))

# V- vector used in processing
V = [0] * 16
def compress(block):
    m=struct.unpack('16%s' % WORDFMT, bytes(block))
    global H

    V[0:8]= H[0:8]
    V[8:15]=IV[0:8]

    for i in range(0, ROUNDS):
        sr=sigma[i]
        Gen(0,4,8,12,0,5,10,15,m[sr[0]],m[sr[1]],m[sr[2]],m[sr[3]])
        
        Gen(1,5,9,13,1,6,11,12,m[sr[4]],m[sr[5]],m[sr[6]],m[sr[7]])
       
        Gen(2,6,10,14,2,7,8,13,m[sr[8]],m[sr[9]],m[sr[10]],m[sr[11]])
        
        Gen(3,7,11,15,3,4,9,14,m[sr[12]],m[sr[13]],m[sr[14]],m[sr[15]])
    H = [H[i]^V[i]^V[i+8] for i in range(8)]
    

def Gen(a,b,c,d,e,f,g,h,x,y,z,w1):
    va = V[a]
    vb = V[b]
    vc = V[c]
    vd = V[d]
    ve=V[e]
    vf=V[f]
    vg=V[g]
    vh=V[h]

    va = (va + vb +x) & MASK32BITS
    w = vd^ va
    vd = (w >> ROT1) | (w << WB_ROT1) & MASK32BITS
    vc= (vc + vd +y) & MASK32BITS
    w = vb ^ vc
    vb = (w >> ROT2) | (w << WB_ROT2) & MASK32BITS
    ve = (ve + vf +z) & MASK32BITS
    w = vh^ ve
    vh = (w >> ROT3) | (w << WB_ROT3) & MASK32BITS
    vg= (vg + vh+w1) & MASK32BITS
    w = vf ^ vg
    vf = (w >> ROT4) | (w << WB_ROT4) & MASK32BITS
          
    V[a]=va
    V[b]=vb
    V[c]=vc
    V[d]=vd
    V[e]=ve
    V[f]=vf
    V[g]=vg
    V[h]=vh
